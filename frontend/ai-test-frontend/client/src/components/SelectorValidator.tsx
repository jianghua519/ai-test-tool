import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Check, X, Loader2, Eye, RefreshCw } from 'lucide-react';
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
  const validationTimeoutRef = useRef<NodeJS.Timeout>();

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

  const validateSelector = async (selectorValue: string) => {
    setValidating(true);
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'VALIDATE_SELECTOR',
        selector: selectorValue,
        url: url
      });

      if (response?.success) {
        setResult({
          valid: response.valid,
          elementCount: response.elementCount || 0,
          selector: selectorValue,
          suggestedSelectors: response.suggestedSelectors || [],
          error: response.error
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
      return null;
    }

    if (result.valid) {
      return (
        <Badge variant="outline" className="text-chart-3 border-chart-3">
          <Check className="mr-1 h-3 w-3" />
          {result.elementCount} {t('cases.elementsFound')}
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

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <Input
          value={selector}
          onChange={(e) => onChange(e.target.value)}
          placeholder={t('cases.selectorPlaceholder')}
          className="flex-1 font-mono text-sm"
        />
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
        <div className="flex items-center space-x-2">
          {getStatusBadge()}
          {!connected && (
            <Badge variant="outline" className="text-muted-foreground">
              {t('cases.extensionNotConnected')}
            </Badge>
          )}
        </div>
        {result?.valid && result.elementCount > 1 && (
          <Badge variant="outline" className="text-chart-4 border-chart-4">
            {t('cases.multipleElementsWarning')}
          </Badge>
        )}
      </div>

      {result?.suggestedSelectors && result.suggestedSelectors.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            {t('cases.suggestedSelectors')}
          </p>
          <div className="space-y-1">
            {result.suggestedSelectors.map((suggested, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-muted/50 rounded hover:bg-muted transition-colors cursor-pointer"
                onClick={() => useSuggestedSelector(suggested)}
              >
                <code className="text-xs font-mono flex-1 truncate">
                  {suggested}
                </code>
                <Button variant="ghost" size="sm" className="ml-2">
                  {t('common.use')}
                </Button>
              </div>
            ))}
          </div>
        </div>
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
