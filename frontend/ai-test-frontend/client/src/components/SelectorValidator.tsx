import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Check, X, Loader2, Eye, RefreshCw, AlertTriangle, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface SelectorValidationResult {
  valid: boolean;
  elementCount: number;
  selector: string;
  suggestedSelectors?: string[];
  error?: string;
  warnings?: string[];
  hints?: string[];
}

interface SelectorValidatorProps {
  selector: string;
  onChange: (selector: string) => void;
  url?: string;
}

export default function SelectorValidator({ selector, onChange, url }: SelectorValidatorProps) {
  const { t } = useTranslation();
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<SelectorValidationResult | null>(null);
  const [highlighting, setHighlighting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [lastValidationTime, setLastValidationTime] = useState<number>(0);
  const validationTimeoutRef = useRef<NodeJS.Timeout>();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    checkExtensionConnection();
    return () => {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (selector && connected) {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
      validationTimeoutRef.current = setTimeout(() => {
        validateSelector(selector);
      }, 500);
    } else {
      setResult(null);
    }
  }, [selector, connected]);

  const checkExtensionConnection = async () => {
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'CHECK_CONNECTION'
      });
      setConnected(response?.connected || false);
    } catch (error) {
      setConnected(false);
    }
  };

  const generateValidationHints = (selectorValue: string, elementCount: number) => {
    const hints: string[] = [];
    const warnings: string[] = [];

    if (!selectorValue.trim()) {
      hints.push('Start typing a CSS selector or XPath');
      return { hints, warnings };
    }

    if (selectorValue.includes(':contains(')) {
      warnings.push(':contains() is not standard CSS and may not work in all browsers');
    }

    if (selectorValue.includes('//') && !selectorValue.startsWith('//')) {
      warnings.push('XPath should start with // or /');
    }

    if (selectorValue.startsWith('#') && elementCount > 1) {
      warnings.push('ID selectors should be unique. Consider using a more specific selector.');
    }

    if (selectorValue.includes('.class') && elementCount > 10) {
      warnings.push('Many elements found with this class. Consider adding more context.');
    }

    if (!selectorValue.includes('#') && !selectorValue.includes('.') && !selectorValue.startsWith('//') && !selectorValue.includes('[')) {
      hints.push('Consider using ID (#id), class (.class), or attributes [attr=value] for more specific selectors');
    }

    if (selectorValue.includes('nth-child(')) {
      hints.push('nth-child() can be brittle. Consider using more stable selectors like IDs or data attributes');
    }

    if (elementCount === 0) {
      hints.push('No elements found. Check the selector or try the browser console to debug');
    }

    return { hints, warnings };
  };

  const validateSelector = async (selectorValue: string) => {
    setValidating(true);
    setLastValidationTime(Date.now());
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'VALIDATE_SELECTOR',
        selector: selectorValue,
        url: url
      });

      if (response?.success) {
        const { hints, warnings } = generateValidationHints(selectorValue, response.elementCount || 0);
        
        setResult({
          valid: response.valid,
          elementCount: response.elementCount || 0,
          selector: selectorValue,
          suggestedSelectors: response.suggestedSelectors || [],
          error: response.error,
          warnings: warnings.length > 0 ? warnings : undefined,
          hints: hints.length > 0 ? hints : undefined
        });
      } else {
        setResult({
          valid: false,
          elementCount: 0,
          selector: selectorValue,
          error: response?.error || 'Validation failed'
        });
      }
    } catch (error) {
      setResult({
        valid: false,
        elementCount: 0,
        selector: selectorValue,
        error: 'Extension not connected'
      });
    } finally {
      setValidating(false);
    }
  };

  const highlightElement = async () => {
    if (!selector || !connected) return;
    
    setHighlighting(true);
    try {
      await chrome.runtime.sendMessage({
        type: 'HIGHLIGHT_ELEMENT',
        selector: selector,
        url: url
      });
      
      setTimeout(() => {
        setHighlighting(false);
      }, 3000);
    } catch (error) {
      console.error('Failed to highlight element:', error);
      setHighlighting(false);
    }
  };

  const useSuggestedSelector = (suggested: string) => {
    onChange(suggested);
  };

  const getStatusBadge = () => {
    if (validating) {
      return (
        <Badge variant="outline" className="text-muted-foreground">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          {t('cases.validating')}
        </Badge>
      );
    }

    if (!result) {
      return (
        <Badge variant="outline" className="text-muted-foreground">
          <Info className="mr-1 h-3 w-3" />
          {t('cases.startTyping')}
        </Badge>
      );
    }

    if (result.valid) {
      return (
        <Badge 
          variant="outline" 
          className={`${
            result.elementCount === 1 
              ? 'text-chart-3 border-chart-3' 
              : 'text-chart-4 border-chart-4'
          }`}
        >
          <Check className="mr-1 h-3 w-3" />
          {result.elementCount} {t('cases.elementsFound')}
          {result.elementCount > 1 && (
            <AlertTriangle className="ml-1 h-3 w-3" />
          )}
        </Badge>
      );
    }

    return (
      <Badge variant="outline" className="text-destructive border-destructive">
        <X className="mr-1 h-3 w-3" />
        {result.error || t('cases.invalidSelector')}
      </Badge>
    );
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    onChange(value);
    
    // Auto-validate after user stops typing for 500ms
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }
    
    validationTimeoutRef.current = setTimeout(() => {
      if (value.trim()) {
        validateSelector(value);
      }
    }, 500);
  };

  const toggleSuggestions = () => {
    setShowSuggestions(!showSuggestions);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <Input
            ref={inputRef}
            value={selector}
            onChange={handleInputChange}
            onFocus={() => selector && validateSelector(selector)}
            placeholder={t('cases.selectorPlaceholder')}
            className={`flex-1 font-mono text-sm ${
              result?.valid 
                ? 'border-chart-3 focus:border-chart-3' 
                : result?.valid === false 
                ? 'border-destructive focus:border-destructive'
                : ''
            }`}
          />
          {selector && (
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              {result?.valid ? (
                <Check className="h-4 w-4 text-chart-3" />
              ) : (
                <X className="h-4 w-4 text-destructive" />
              )}
            </div>
          )}
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                onClick={validateSelector}
                disabled={!selector || !connected}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t('cases.validateSelector')}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                onClick={highlightElement}
                disabled={!selector || !connected || !result?.valid || highlighting}
              >
                <Eye className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t('cases.highlightElement')}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 flex-wrap gap-2">
          {getStatusBadge()}
          {!connected && (
            <Badge variant="outline" className="text-muted-foreground">
              {t('cases.extensionNotConnected')}
            </Badge>
          )}
          {result?.warnings && result.warnings.length > 0 && (
            <Badge variant="outline" className="text-amber-600 border-amber-600">
              <AlertTriangle className="mr-1 h-3 w-3" />
              {result.warnings.length} {t('cases.warnings')}
            </Badge>
          )}
        </div>
        {result?.suggestedSelectors && result.suggestedSelectors.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSuggestions}
            className="text-xs"
          >
            {showSuggestions ? 'Hide' : 'Show'} suggestions
          </Button>
        )}
      </div>

      <AnimatePresence>
        {result?.hints && result.hints.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-3 bg-blue-50 border border-blue-200 rounded-lg"
          >
            <div className="flex items-start space-x-2">
              <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-blue-800">
                  {t('cases.tips')}
                </p>
                <ul className="text-xs text-blue-700 space-y-1">
                  {result.hints.map((hint, index) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2">•</span>
                      {hint}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        )}

        {result?.warnings && result.warnings.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-3 bg-amber-50 border border-amber-200 rounded-lg"
          >
            <div className="flex items-start space-x-2">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-amber-800">
                  {t('cases.important')}
                </p>
                <ul className="text-xs text-amber-700 space-y-1">
                  {result.warnings.map((warning, index) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2">•</span>
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {showSuggestions && result?.suggestedSelectors && result.suggestedSelectors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
          className="space-y-2"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">
              {t('cases.suggestedSelectors')}
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSuggestions}
              className="text-xs"
            >
              Hide
            </Button>
          </div>
          <div className="space-y-1 border border-dashed border-muted-foreground/30 rounded-lg p-2">
            {result.suggestedSelectors.map((suggested, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center justify-between p-2 bg-muted/50 rounded hover:bg-muted transition-colors cursor-pointer group"
                onClick={() => useSuggestedSelector(suggested)}
              >
                <code className="text-xs font-mono flex-1 truncate group-hover:text-blue-600 transition-colors">
                  {suggested}
                </code>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="ml-2 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  {t('common.use')}
                </Button>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {highlighting && (
        <div className="p-3 bg-chart-3/10 border border-chart-3/20 rounded-lg">
          <p className="text-sm text-chart-3 flex items-center">
            <Eye className="mr-2 h-4 w-4" />
            {t('cases.elementHighlighted')}
          </p>
        </div>
      )}
    </div>
  );
}
