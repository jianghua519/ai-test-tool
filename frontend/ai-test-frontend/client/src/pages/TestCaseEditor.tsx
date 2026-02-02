import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useLocation } from 'wouter';
import {
  Save,
  Play,
  Plus,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
  Bot,
  ArrowLeft,
  Move
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import DashboardLayout from '@/components/DashboardLayout';
import SelectorValidator from '@/components/SelectorValidator';
import AssertionBuilder from '@/components/AssertionBuilder';
import VariableManager from '@/components/VariableManager';

interface TestStep {
  id: string;
  name: string;
  action: string;
  selector: string;
  value?: string;
  enabled: boolean;
}

interface Assertion {
  id: string;
  type: string;
  value: string;
  description: string;
}

interface TestCase {
  id?: number;
  name: string;
  description: string;
  steps: TestStep[];
  assertions: Assertion[];
  variables: Record<string, string>;
}

const ACTION_TYPES = [
  { value: 'navigate', label: 'Navigate' },
  { value: 'click', label: 'Click' },
  { value: 'type', label: 'Type' },
  { value: 'select', label: 'Select' },
  { value: 'check', label: 'Check' },
  { value: 'uncheck', label: 'Uncheck' },
  { value: 'wait', label: 'Wait' },
  { value: 'waitForSelector', label: 'Wait For Selector' },
];

const ASSERTION_TYPES = [
  { value: 'urlContains', label: 'URL Contains' },
  { value: 'textVisible', label: 'Text Visible' },
  { value: 'elementExists', label: 'Element Exists' },
  { value: 'elementVisible', label: 'Element Visible' },
];

export default function TestCaseEditor() {
  const { t } = useTranslation();
  const { id } = useParams();
  const [, navigate] = useLocation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testCase, setTestCase] = useState<TestCase>({
    name: '',
    description: '',
    steps: [],
    assertions: [],
    variables: {},
  });
  const [draggedItem, setDraggedItem] = useState<{
    id: string;
    index: number;
    content: React.ReactNode;
  } | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [draggedStep, setDraggedStep] = useState<string | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);

  useEffect(() => {
    if (id) {
      fetchTestCase(id);
    } else {
      setLoading(false);
    }
  }, [id]);

  const fetchTestCase = async (caseId: string) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/cases/${caseId}`
      );
      if (response.ok) {
        const data = await response.json();
        setTestCase({
          id: data.id,
          name: data.name,
          description: data.description,
          steps: data.steps || [],
          assertions: data.assertions || [],
          variables: data.variables || {},
        });
      }
    } catch (error) {
      console.error('Failed to fetch test case:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const url = id
        ? `${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/cases/${id}`
        : `${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/cases`;
      
      const method = id ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testCase),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (!id) {
          navigate(`/test-cases/${data.id}`);
        }
      }
    } catch (error) {
      console.error('Failed to save test case:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleRun = async () => {
    if (!id) return;
    
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/exec/run`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ case_id: parseInt(id) }),
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        navigate(`/test-runs/${result.run_id}`);
      }
    } catch (error) {
      console.error('Failed to run test case:', error);
    }
  };

  const addStep = () => {
    const newStep: TestStep = {
      id: `step-${Date.now()}`,
      name: `Step ${testCase.steps.length + 1}`,
      action: 'click',
      selector: '',
      enabled: true,
    };
    setTestCase({
      ...testCase,
      steps: [...testCase.steps, newStep],
    });
    setExpandedSteps(new Set([...expandedSteps, newStep.id]));
  };

  const updateStep = (stepId: string, updates: Partial<TestStep>) => {
    setTestCase({
      ...testCase,
      steps: testCase.steps.map((step) =>
        step.id === stepId ? { ...step, ...updates } : step
      ),
    });
  };

  const deleteStep = (stepId: string) => {
    setTestCase({
      ...testCase,
      steps: testCase.steps.filter((step) => step.id !== stepId),
    });
    setExpandedSteps(new Set([...expandedSteps].filter((id) => id !== stepId)));
  };

  const toggleStepEnabled = (stepId: string) => {
    setTestCase({
      ...testCase,
      steps: testCase.steps.map((step) =>
        step.id === stepId ? { ...step, enabled: !step.enabled } : step
      ),
    });
  };

  const toggleStepExpanded = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const handleDragStart = (stepId: string, index: number) => {
    setDraggedStep(stepId);
    setDragIndex(index);
    // Store the dragged item for preview
    const step = testCase.steps.find(s => s.id === stepId);
    if (step) {
      setDraggedItem({
        id: stepId,
        index,
        content: (
          <div className="flex items-center p-3 bg-white border rounded-lg shadow-lg">
            <div className="flex items-center justify-center w-6 h-6 mr-2 text-muted-foreground">
              <Move className="h-4 w-4" />
            </div>
            <span className="text-sm font-medium">Step {index + 1}</span>
            <Badge variant="outline" className="ml-2">{step.action}</Badge>
          </div>
        ),
      });
    }
  };

  const handleDragEnd = () => {
    setDraggedStep(null);
    setDragIndex(null);
    setDraggedItem(null);
  };

  const moveStep = (fromIndex: number, toIndex: number) => {
    const newSteps = [...testCase.steps];
    const [movedStep] = newSteps.splice(fromIndex, 1);
    newSteps.splice(toIndex, 0, movedStep);
    setTestCase({ ...testCase, steps: newSteps });
  };

  const handleAssertionsChange = (newAssertions: Assertion[]) => {
    setTestCase({
      ...testCase,
      assertions: newAssertions,
    });
  };

  const handleVariablesChange = (newVariables: Record<string, string>) => {
    setTestCase({
      ...testCase,
      variables: newVariables,
    });
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">{t('common.loading')}</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Drag Preview Overlay */}
      <AnimatePresence>
        {draggedItem && (
          <motion.div
            className="fixed top-4 right-4 z-50"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            {draggedItem.content}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/test-cases')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-3xl font-display font-bold text-foreground">
              {id ? t('cases.editTitle') : t('cases.createTitle')}
            </h1>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleRun} disabled={!id}>
              <Play className="mr-2 h-4 w-4" />
              {t('common.run')}
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? t('common.saving') : t('common.save')}
            </Button>
                      </motion.div>
                      </motion.div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            <div>
              <label className="text-sm font-medium mb-2 block">{t('cases.description')}</label>
              <Textarea
                value={testCase.description}
                onChange={(e) => setTestCase({ ...testCase, description: e.target.value })}
                placeholder={t('cases.descriptionPlaceholder')}
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{t('cases.steps')}</CardTitle>
              <Button size="sm" onClick={addStep}>
                <Plus className="mr-2 h-4 w-4" />
                {t('cases.addStep')}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {testCase.steps.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {t('cases.noSteps')}
              </div>
            ) : (
              <div className="space-y-2">
                <AnimatePresence>
                  {testCase.steps.map((step, index) => (
                    <motion.div
                      key={step.id}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.2 }}
                      className={`border rounded-lg transition-all ${
                        !step.enabled ? 'opacity-60' : ''
                      } ${dragIndex === index ? 'ring-2 ring-blue-400 bg-blue-50' : ''}`}
                      whileDrag={{
                        scale: 1.02,
                        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                      }}
                    >
                      <motion.div
                        draggable
                        onDragStart={() => handleDragStart(step.id, index)}
                        onDragEnd={handleDragEnd}
                        className="flex items-center p-3 cursor-grab active:cursor-grabbing"
                      >
                    <div className="flex items-center p-3">
                      <motion.div
                        className="flex items-center p-3 cursor-grab active:cursor-grabbing"
                        whileHover={{ backgroundColor: 'rgba(59, 130, 246, 0.05)' }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <div className="flex items-center justify-center w-6 h-6 mr-2 text-muted-foreground">
                          <Move className="h-4 w-4" />
                        </div>
                        <Button
                        variant="ghost"
                        size="icon"
                        className="mr-2"
                        onClick={() => toggleStepExpanded(step.id)}
                      >
                        {expandedSteps.has(step.id) && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.2 }}
                            className="px-3 pb-3 space-y-3 border-t pt-3"
                        <div>
                          <label className="text-sm font-medium mb-2 block">{t('cases.action')}</label>
                          <Select
                            value={step.action}
                            onValueChange={(value) => updateStep(step.id, { action: value })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {ACTION_TYPES.map((type) => (
                                <SelectItem key={type.value} value={type.value}>
                                  {type.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-2 block">{t('cases.selector')}</label>
                          <SelectorValidator
                            selector={step.selector}
                            onChange={(value) => updateStep(step.id, { selector: value })}
                          />
                        </div>
                        {(step.action === 'type' ||
                          step.action === 'select' ||
                          step.action === 'navigate' ||
                          step.action === 'wait') && (
                          <div>
                            <label className="text-sm font-medium mb-2 block">{t('cases.value')}</label>
                            <Input
                              value={step.value || ''}
                              onChange={(e) => updateStep(step.id, { value: e.target.value })}
                              placeholder={t('cases.valuePlaceholder')}
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('cases.assertions')}</CardTitle>
          </CardHeader>
          <CardContent>
            <AssertionBuilder
              assertions={testCase.assertions}
              onAssertionsChange={handleAssertionsChange}
              variables={testCase.variables}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('cases.variables')}</CardTitle>
          </CardHeader>
          <CardContent>
            <VariableManager
              variables={testCase.variables}
              onVariablesChange={handleVariablesChange}
            />
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
