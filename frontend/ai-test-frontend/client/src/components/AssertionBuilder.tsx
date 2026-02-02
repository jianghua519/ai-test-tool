import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Plus, 
  Trash2, 
  GripVertical, 
  Move,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Save,
  Play
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface AssertionRule {
  id: string;
  type: string;
  operator: string;
  value: string;
  negate: boolean;
  description: string;
}

interface AssertionGroup {
  id: string;
  name: string;
  rules: AssertionRule[];
  logic: 'AND' | 'OR';
  enabled: boolean;
}

interface AssertionBuilderProps {
  assertions: Assertion[];
  onAssertionsChange: (assertions: Assertion[]) => void;
  variables: Record<string, string>;
}

const ASSERTION_TYPES = [
  { value: 'urlContains', label: 'URL Contains', description: 'Check if URL contains text' },
  { value: 'urlEquals', label: 'URL Equals', description: 'Check if URL exactly matches' },
  { value: 'urlMatches', label: 'URL Matches Pattern', description: 'Check if URL matches regex pattern' },
  { value: 'textVisible', label: 'Text Visible', description: 'Check if text is visible on page' },
  { value: 'textContains', label: 'Text Contains', description: 'Check if element contains text' },
  { value: 'textEquals', label: 'Text Equals', description: 'Check if element text exactly matches' },
  { value: 'elementExists', label: 'Element Exists', description: 'Check if element exists in DOM' },
  { value: 'elementVisible', label: 'Element Visible', description: 'Check if element is visible' },
  { value: 'elementHidden', label: 'Element Hidden', description: 'Check if element is hidden' },
  { value: 'elementContains', label: 'Element Contains', description: 'Check if element contains specific text' },
  { value: 'attributeExists', label: 'Attribute Exists', description: 'Check if element has attribute' },
  { value: 'attributeEquals', label: 'Attribute Equals', description: 'Check if attribute value matches' },
  { value: 'titleContains', label: 'Title Contains', description: 'Check if page title contains text' },
  { value: 'titleEquals', label: 'Title Equals', description: 'Check if page title exactly matches' },
  { value: 'checkboxChecked', label: 'Checkbox Checked', description: 'Check if checkbox is checked' },
  { value: 'checkboxUnchecked', label: 'Checkbox Unchecked', description: 'Check if checkbox is unchecked' },
];

const OPERATORS = [
  { value: 'equals', label: 'Equals', icon: '=' },
  { value: 'notEquals', label: 'Not Equals', icon: '≠' },
  { value: 'contains', label: 'Contains', icon: '∋' },
  { value: 'notContains', label: 'Not Contains', icon: '∌' },
  { value: 'startsWith', label: 'Starts With', icon: '↗' },
  { value: 'endsWith', label: 'Ends With', icon: '↙' },
  { value: 'matches', label: 'Matches Pattern', icon: '~' },
  { value: 'greaterThan', label: 'Greater Than', icon: '>' },
  { value: 'lessThan', label: 'Less Than', icon: '<' },
  { value: 'greaterThanOrEquals', label: 'Greater or Equal', icon: '≥' },
  { value: 'lessThanOrEquals', label: 'Less or Equal', icon: '≤' },
];

export default function AssertionBuilder({ assertions, onAssertionsChange, variables }: AssertionBuilderProps) {
  const { t } = useTranslation();
  const [groups, setGroups] = useState<AssertionGroup[]>(
    assertions.map((assertion, index) => ({
      id: `group-${index}`,
      name: `Assertion ${index + 1}`,
      rules: [{
        id: assertion.id,
        type: assertion.type,
        operator: 'equals',
        value: assertion.value,
        negate: false,
        description: assertion.description,
      }],
      logic: 'AND',
      enabled: true,
    }))
  );
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [newGroupName, setNewGroupName] = useState('');
  const [draggedRule, setDraggedRule] = useState<{ groupId: string; ruleIndex: number } | null>(null);
  const [showNewGroupDialog, setShowNewGroupDialog] = useState(false);
  const [selectedVariables, setSelectedVariables] = useState<string[]>([]);
  const variableDropdownRef = useRef<HTMLDivElement>(null);

  const addNewGroup = () => {
    if (!newGroupName.trim()) return;

    const newGroup: AssertionGroup = {
      id: `group-${Date.now()}`,
      name: newGroupName,
      rules: [],
      logic: 'AND',
      enabled: true,
    };

    setGroups([...groups, newGroup]);
    setExpandedGroups(new Set([...expandedGroups, newGroup.id]));
    setNewGroupName('');
    setShowNewGroupDialog(false);
  };

  const addRuleToGroup = (groupId: string) => {
    const updatedGroups = groups.map(group => {
      if (group.id === groupId) {
        const newRule: AssertionRule = {
          id: `rule-${Date.now()}`,
          type: 'textVisible',
          operator: 'equals',
          value: '',
          negate: false,
          description: '',
        };
        return {
          ...group,
          rules: [...group.rules, newRule],
        };
      }
      return group;
    });
    setGroups(updatedGroups);
  };

  const updateRule = (groupId: string, ruleIndex: number, updates: Partial<AssertionRule>) => {
    const updatedGroups = groups.map(group => {
      if (group.id === groupId) {
        const updatedRules = [...group.rules];
        updatedRules[ruleIndex] = { ...updatedRules[ruleIndex], ...updates };
        return { ...group, rules: updatedRules };
      }
      return group;
    });
    setGroups(updatedGroups);
  };

  const deleteRule = (groupId: string, ruleIndex: number) => {
    const updatedGroups = groups.map(group => {
      if (group.id === groupId) {
        const updatedRules = group.rules.filter((_, index) => index !== ruleIndex);
        return { ...group, rules: updatedRules };
      }
      return group;
    });
    setGroups(updatedGroups);
  };

  const deleteGroup = (groupId: string) => {
    const updatedGroups = groups.filter(group => group.id !== groupId);
    setGroups(updatedGroups);
    setExpandedGroups(new Set([...expandedGroups].filter(id => id !== groupId)));
  };

  const toggleGroupLogic = (groupId: string) => {
    const updatedGroups = groups.map(group => {
      if (group.id === groupId) {
        return {
          ...group,
          logic: group.logic === 'AND' ? 'OR' : 'AND',
        };
      }
      return group;
    });
    setGroups(updatedGroups);
  };

  const toggleGroupEnabled = (groupId: string) => {
    const updatedGroups = groups.map(group => {
      if (group.id === groupId) {
        return {
          ...group,
          enabled: !group.enabled,
        };
      }
      return group;
    });
    setGroups(updatedGroups);
  };

  const toggleGroupExpanded = (groupId: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  const handleDragStart = (groupId: string, ruleIndex: number) => {
    setDraggedRule({ groupId, ruleIndex });
  };

  const handleDragOver = (e: React.DragEvent, groupId: string, ruleIndex: number) => {
    e.preventDefault();
    if (!draggedRule || draggedRule.groupId === groupId) return;

    const updatedGroups = [...groups];
    const sourceGroup = updatedGroups.find(g => g.id === draggedRule.groupId);
    const targetGroup = updatedGroups.find(g => g.id === groupId);

    if (sourceGroup && targetGroup) {
      const [movedRule] = sourceGroup.rules.splice(draggedRule.ruleIndex, 1);
      targetGroup.rules.splice(ruleIndex, 0, movedRule);
      
      setGroups(updatedGroups);
      setDraggedRule({ groupId, ruleIndex });
    }
  };

  const handleDragEnd = () => {
    setDraggedRule(null);
  };

  const handleSave = () => {
    const newAssertions: Assertion[] = [];
    
    groups.forEach(group => {
      if (group.rules.length > 0) {
        group.rules.forEach(rule => {
          if (rule.value.trim()) {
            newAssertions.push({
              id: rule.id,
              type: rule.type,
              value: rule.value,
              description: rule.description || `${rule.type}: ${rule.value}`,
            });
          }
        });
      }
    });

    onAssertionsChange(newAssertions);
  };

  const getAssertionIcon = (type: string) => {
    switch (type) {
      case 'urlContains':
      case 'textVisible':
      case 'titleContains':
        return CheckCircle;
      case 'elementExists':
      case 'elementVisible':
        return CheckCircle;
      default:
        return CheckCircle;
    }
  };

  const getOperatorIcon = (operator: string) => {
    const op = OPERATORS.find(o => o.value === operator);
    return op ? op.icon : '=';
  };

  const getAssertionLabel = (type: string) => {
    const assertion = ASSERTION_TYPES.find(a => a.value === type);
    return assertion ? assertion.label : type;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">{t('cases.assertions')}</h3>
        <Dialog open={showNewGroupDialog} onOpenChange={setShowNewGroupDialog}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" />
              Add Group
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Assertion Group</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Group Name</label>
                <Input
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  placeholder="Enter group name..."
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowNewGroupDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={addNewGroup}>
                  Create Group
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-3">
        {groups.map((group, groupIndex) => (
          <motion.div
            key={group.id}
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className={`border rounded-lg transition-all ${
              !group.enabled ? 'opacity-60 bg-muted/30' : ''
            }`}
          >
            <div
              className="flex items-center p-3 cursor-pointer"
              onClick={() => toggleGroupExpanded(group.id)}
            >
              <Button variant="ghost" size="icon" className="mr-2">
                {expandedGroups.has(group.id) ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
              <div className="flex items-center space-x-2 flex-1">
                <div className="flex items-center justify-center w-6 h-6 mr-2 text-muted-foreground">
                  <CheckCircle className="h-4 w-4" />
                </div>
                <Input
                  value={group.name}
                  onChange={(e) => {
                    const updatedGroups = groups.map(g => 
                      g.id === group.id ? { ...g, name: e.target.value } : g
                    );
                    setGroups(updatedGroups);
                  }}
                  className="flex-1"
                />
                <Badge variant="outline" className="cursor-pointer" onClick={(e) => {
                  e.stopPropagation();
                  toggleGroupLogic(group.id);
                }}>
                  {group.logic}
                </Badge>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleGroupEnabled(group.id);
                  }}
                >
                  {group.enabled ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteGroup(group.id);
                  }}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <AnimatePresence>
              {expandedGroups.has(group.id) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="px-3 pb-3 space-y-2 border-t"
                >
                  <div className="flex items-center justify-between p-2 bg-muted/50 rounded">
                    <span className="text-sm font-medium">Rules</span>
                    <Button
                      size="sm"
                      onClick={() => addRuleToGroup(group.id)}
                    >
                      <Plus className="mr-1 h-3 w-3" />
                      Add Rule
                    </Button>
                  </div>

                  {group.rules.length === 0 ? (
                    <div className="text-center py-4 text-muted-foreground text-sm">
                      No rules in this group. Add a rule to get started.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {group.rules.map((rule, ruleIndex) => {
                        const IconComponent = getAssertionIcon(rule.type);
                        return (
                          <motion.div
                            key={rule.id}
                            draggable
                            onDragStart={() => handleDragStart(group.id, ruleIndex)}
                            onDragOver={(e) => handleDragOver(e, group.id, ruleIndex)}
                            onDragEnd={handleDragEnd}
                            className={`p-3 border rounded-lg transition-all ${
                              draggedRule?.groupId === group.id && draggedRule?.ruleIndex === ruleIndex
                                ? 'ring-2 ring-blue-400 bg-blue-50'
                                : ''
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <div className="flex items-center justify-center w-6 h-6 text-muted-foreground">
                                <GripVertical className="h-4 w-4" />
                              </div>
                              <div className="flex items-center justify-center w-6 h-6">
                                <IconComponent className="h-4 w-4 text-blue-600" />
                              </div>
                              <Select
                                value={rule.type}
                                onValueChange={(value) => updateRule(group.id, ruleIndex, { type: value })}
                              >
                                <SelectTrigger className="flex-1">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {ASSERTION_TYPES.map((type) => (
                                    <SelectItem key={type.value} value={type.value}>
                                      {type.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              <Badge variant="outline" className="w-12 text-center">
                                {getOperatorIcon(rule.operator)}
                              </Badge>
                              <div className="flex-1 relative">
                                <Input
                                  value={rule.value}
                                  onChange={(e) => updateRule(group.id, ruleIndex, { value: e.target.value })}
                                  placeholder={getAssertionLabel(rule.type) === 'URL Contains' ? 'Enter URL fragment...' : 'Enter expected value...'}
                                  className="pr-8"
                                />
                                {Object.keys(variables).length > 0 && (
                                  <Select
                                    value={selectedVariables[ruleIndex] || ''}
                                    onValueChange={(value) => {
                                      const newSelected = [...selectedVariables];
                                      newSelected[ruleIndex] = value;
                                      setSelectedVariables(newSelected);
                                      updateRule(group.id, ruleIndex, { value: value });
                                    }}
                                  >
                                    <SelectTrigger className="absolute top-0 right-0 w-20 h-full">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="">Static</SelectItem>
                                      {Object.entries(variables).map(([key, value]) => (
                                        <SelectItem key={key} value={`{{${key}}}`}>
                                          {key}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                )}
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => deleteRule(group.id, ruleIndex)}
                                className="text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                            {rule.description && (
                              <div className="mt-2">
                                <Input
                                  value={rule.description}
                                  onChange={(e) => updateRule(group.id, ruleIndex, { description: e.target.value })}
                                  placeholder="Description..."
                                  className="text-sm"
                                />
                              </div>
                            )}
                          </motion.div>
                        );
                      })}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {groups.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No assertion groups created. Create a group to start building assertions.
        </div>
      )}

      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={handleSave}>
          <Save className="mr-2 h-4 w-4" />
          Save Assertions
        </Button>
      </div>
    </div>
  );
}