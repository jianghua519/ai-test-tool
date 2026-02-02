import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Plus, 
  Trash2, 
  Edit3, 
  Save, 
  X, 
  Calculator, 
  Database,
  Copy,
  Download,
  Upload,
  Eye,
  AlertCircle,
  CheckCircle,
  Function,
  Variable
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface Variable {
  id: string;
  name: string;
  value: string;
  type: 'static' | 'expression' | 'function';
  description: string;
  category: string;
  encrypted: boolean;
  references: string[];
}

interface VariableManagerProps {
  variables: Record<string, string>;
  onVariablesChange: (variables: Record<string, string>) => void;
}

const BUILTIN_FUNCTIONS = [
  { name: 'generateRandomString', params: ['length'], description: 'Generate random string of specified length' },
  { name: 'generateRandomNumber', params: ['min', 'max'], description: 'Generate random number between min and max' },
  { name: 'generateEmail', params: ['domain'], description: 'Generate random email address' },
  { name: 'generateDate', params: ['format?'], description: 'Generate current or formatted date' },
  { name: 'generateUUID', params: [], description: 'Generate UUID' },
  { name: 'base64Encode', params: ['text'], description: 'Base64 encode text' },
  { name: 'base64Decode', params: ['text'], description: 'Base64 decode text' },
  { name: 'md5Hash', params: ['text'], description: 'Generate MD5 hash' },
  { name: 'sha256Hash', params: ['text'], description: 'Generate SHA-256 hash' },
];

const VARIABLE_CATEGORIES = [
  'Authentication',
  'User Data',
  'Test Data',
  'Configuration',
  'Environment',
  'Generated',
  'Constants'
];

export default function VariableManager({ variables, onVariablesChange }: VariableManagerProps) {
  const { t } = useTranslation();
  const [variableList, setVariableList] = useState<Variable[]>(
    Object.entries(variables).map(([key, value], index) => ({
      id: `var-${index}`,
      name: key,
      value,
      type: 'static',
      description: '',
      category: 'General',
      encrypted: false,
      references: [],
    }))
  );
  const [editingVariable, setEditingVariable] = useState<Variable | null>(null);
  const [newVariable, setNewVariable] = useState<Partial<Variable>>({
    name: '',
    value: '',
    type: 'static',
    description: '',
    category: 'General',
    encrypted: false,
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [expressionPreview, setExpressionPreview] = useState<{ valid: boolean; result?: string; error?: string }>({
    valid: true
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateExpression = (expression: string): { valid: boolean; result?: string; error?: string } => {
    if (!expression.trim()) {
      return { valid: true };
    }

    try {
      // Basic expression validation
      const testExpression = expression.replace(/\{\{([^}]+)\}\}/g, 'testValue');
      // eslint-disable-next-eval
      const result = Function('"use strict"; return (' + testExpression + ')')();
      
      return { 
        valid: true, 
        result: typeof result === 'string' ? result : JSON.stringify(result),
        error: undefined 
      };
    } catch (error) {
      return { 
        valid: false, 
        error: error instanceof Error ? error.message : 'Invalid expression'
      };
    }
  };

  const addVariable = () => {
    if (!newVariable.name?.trim() || !newVariable.value?.trim()) return;

    const updatedVariables = { ...variables };
    updatedVariables[newVariable.name] = newVariable.value;
    onVariablesChange(updatedVariables);

    setVariableList([
      ...variableList,
      {
        id: `var-${Date.now()}`,
        name: newVariable.name,
        value: newVariable.value,
        type: newVariable.type as 'static' | 'expression' | 'function',
        description: newVariable.description || '',
        category: newVariable.category || 'General',
        encrypted: newVariable.encrypted || false,
        references: [],
      }
    ]);

    setNewVariable({
      name: '',
      value: '',
      type: 'static',
      description: '',
      category: 'General',
      encrypted: false,
    });
  };

  const updateVariable = (updatedVariable: Variable) => {
    const updatedVariables = { ...variables };
    delete updatedVariables[updatedVariable.name];
    
    if (updatedVariable.value.trim()) {
      updatedVariables[updatedVariable.name] = updatedVariable.value;
    }
    
    onVariablesChange(updatedVariables);

    setVariableList(
      variableList.map(var => 
        var.id === updatedVariable.id ? updatedVariable : var
      ).filter(var => var.value.trim())
    );
    setEditingVariable(null);
  };

  const deleteVariable = (variableName: string) => {
    const updatedVariables = { ...variables };
    delete updatedVariables[variableName];
    onVariablesChange(updatedVariables);

    setVariableList(variableList.filter(var => var.name !== variableName));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportVariables = () => {
    const dataStr = JSON.stringify(variables, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `variables-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const importedVariables = JSON.parse(content);
        
        // Validate and merge variables
        const updatedVariables = { ...variables, ...importedVariables };
        onVariablesChange(updatedVariables);

        // Update variable list
        setVariableList([
          ...variableList,
          ...Object.entries(importedVariables).map(([key, value], index) => ({
            id: `var-import-${Date.now()}-${index}`,
            name: key,
            value: value.toString(),
            type: 'static',
            description: 'Imported',
            category: 'Imported',
            encrypted: false,
            references: [],
          }))
        ]);

        alert('Variables imported successfully!');
      } catch (error) {
        alert('Failed to import variables. Invalid JSON file.');
      }
    };
    reader.readAsText(file);
  };

  const filteredVariables = variableList.filter(var => {
    const matchesSearch = var.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         var.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || var.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const variablesByCategory = filteredVariables.reduce((acc, varItem) => {
    if (!acc[varItem.category]) {
      acc[varItem.category] = [];
    }
    acc[varItem.category].push(varItem);
    return acc;
  }, {} as Record<string, Variable[]>);

  const categories = ['All', ...VARIABLE_CATEGORIES.filter(cat => 
    filteredVariables.some(var => var.category === cat)
  )];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium flex items-center">
          <Variable className="mr-2 h-5 w-5" />
          {t('cases.variables')}
        </h3>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={exportVariables}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Dialog>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Variable
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add New Variable</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <Tabs value={newVariable.type} onValueChange={(value) => setNewVariable({...newVariable, type: value as any})}>
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="static">Static</TabsTrigger>
                    <TabsTrigger value="expression">Expression</TabsTrigger>
                    <TabsTrigger value="function">Function</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="static" className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Variable Name</label>
                      <Input
                        value={newVariable.name || ''}
                        onChange={(e) => setNewVariable({...newVariable, name: e.target.value})}
                        placeholder="e.g., username, password"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Value</label>
                      <Textarea
                        value={newVariable.value || ''}
                        onChange={(e) => setNewVariable({...newVariable, value: e.target.value})}
                        placeholder="Enter static value..."
                        rows={3}
                      />
                    </div>
                  </TabsContent>

                  <TabsContent value="expression" className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Variable Name</label>
                      <Input
                        value={newVariable.name || ''}
                        onChange={(e) => setNewVariable({...newVariable, name: e.target.value})}
                        placeholder="e.g., current_time"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Expression</label>
                      <Textarea
                        value={newVariable.value || ''}
                        onChange={(e) => {
                          const value = e.target.value;
                          setNewVariable({...newVariable, value});
                          setExpressionPreview(validateExpression(value));
                        }}
                        placeholder="e.g., {{current_date}} + 'T' + {{current_time}}"
                        rows={3}
                        className="font-mono"
                      />
                      {expressionPreview.error && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600 flex items-center">
                          <AlertCircle className="mr-1 h-4 w-4" />
                          {expressionPreview.error}
                        </div>
                      )}
                      {expressionPreview.result && (
                        <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-600 flex items-center">
                          <CheckCircle className="mr-1 h-4 w-4" />
                          Preview: {expressionPreview.result}
                        </div>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="function" className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Function Name</label>
                      <Select onValueChange={(value) => setNewVariable({...newVariable, value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a function..." />
                        </SelectTrigger>
                        <SelectContent>
                          {BUILTIN_FUNCTIONS.map((func) => (
                            <SelectItem key={func.name} value={`${func.name}(${func.params.join(', ')})`}>
                              {func.name}({func.params.join(', ')})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {BUILTIN_FUNCTIONS.find(f => newVariable.value?.includes(f.name))?.description}
                    </div>
                  </TabsContent>
                </Tabs>

                <div>
                  <label className="text-sm font-medium mb-2 block">Category</label>
                  <Select 
                    value={newVariable.category} 
                    onValueChange={(value) => setNewVariable({...newVariable, category: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VARIABLE_CATEGORIES.map(category => (
                        <SelectItem key={category} value={category}>
                          {category}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Description</label>
                  <Input
                    value={newVariable.description || ''}
                    onChange={(e) => setNewVariable({...newVariable, description: e.target.value})}
                    placeholder="Optional description..."
                  />
                </div>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setNewVariable({
                    name: '',
                    value: '',
                    type: 'static',
                    description: '',
                    category: 'General',
                    encrypted: false,
                  })}>
                    Clear
                  </Button>
                  <Button onClick={addVariable}>
                    Add Variable
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex space-x-4">
        <div className="flex-1">
          <Input
            placeholder="Search variables..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {categories.map(category => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-4">
        {categories.filter(cat => cat !== 'All').map(category => (
          variablesByCategory[category] && variablesByCategory[category].length > 0 && (
            <div key={category}>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">{category}</h4>
              <div className="grid gap-3">
                {variablesByCategory[category].map(variable => (
                  <motion.div
                    key={variable.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    className="p-3 border rounded-lg group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <Variable className="h-4 w-4 text-blue-600" />
                          <Input
                            value={variable.name}
                            onChange={(e) => {
                              const updated = {...variable, name: e.target.value};
                              setVariableList(variableList.map(v => v.id === variable.id ? updated : v));
                            }}
                            className="font-mono text-sm border-none p-0 h-auto focus-visible:ring-0"
                          />
                          <Badge variant="outline" className="text-xs">
                            {variable.type}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {variable.category}
                          </Badge>
                          {variable.encrypted && (
                            <Badge variant="destructive" className="text-xs">
                              Encrypted
                            </Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2 mb-2">
                          {editingVariable?.id === variable.id ? (
                            <Textarea
                              value={variable.value}
                              onChange={(e) => {
                                const updated = {...variable, value: e.target.value};
                                setVariableList(variableList.map(v => v.id === variable.id ? updated : v));
                              }}
                              className="font-mono text-sm flex-1"
                              rows={2}
                            />
                          ) : (
                            <>
                              <div className="flex-1">
                                <code className="text-xs bg-muted p-1 rounded font-mono">
                                  {variable.value}
                                </code>
                              </div>
                            </>
                          )}
                          
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => copyToClipboard(variable.value)}
                                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Copy value</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                        
                        {variable.description && (
                          <p className="text-xs text-muted-foreground mb-2">
                            {variable.description}
                          </p>
                        )}
                        
                        <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingVariable(editingVariable?.id === variable.id ? null : variable)}
                          >
                            {editingVariable?.id === variable.id ? (
                              <CheckCircle className="h-3 w-3" />
                            ) : (
                              <Edit3 className="h-3 w-3" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteVariable(variable.name)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )
        ))}
      </div>

      {filteredVariables.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No variables found. Add a variable to get started.
        </div>
      )}

      <AnimatePresence>
        {showAdvanced && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-4 border rounded-lg bg-muted/50"
          >
            <h4 className="text-sm font-medium mb-3">Advanced Usage</h4>
            <div className="space-y-3 text-xs">
              <div>
                <code className="bg-background px-2 py-1 rounded">variable_name</code>
                <span className="ml-2 text-muted-foreground">Reference a variable in expressions</span>
              </div>
              <div>
                <code className="bg-background px-2 py-1 rounded">function_name()</code>
                <span className="ml-2 text-muted-foreground">Call built-in functions</span>
              </div>
              <div>
                <code className="bg-background px-2 py-1 rounded">{{variable}}</code>
                <span className="ml-2 text-muted-foreground">Variable interpolation</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}