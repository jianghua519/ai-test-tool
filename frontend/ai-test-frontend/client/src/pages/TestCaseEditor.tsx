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
  ArrowLeft
} from 'lucide-react';
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
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [draggedStep, setDraggedStep] = useState<string | null>(null);
  const [showAssertionDialog, setShowAssertionDialog] = useState(false);
  const [newAssertion, setNewAssertion] = useState<Assertion>({
    id: '',
    type: 'urlContains',
    value: '',
    description: '',
  });

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

  const handleDragStart = (stepId: string) => {
    setDraggedStep(stepId);
  };

  const handleDragOver = (e: React.DragEvent, targetStepId: string) => {
    e.preventDefault();
    if (!draggedStep || draggedStep === targetStepId) return;

    const steps = [...testCase.steps];
    const draggedIndex = steps.findIndex((s) => s.id === draggedStep);
    const targetIndex = steps.findIndex((s) => s.id === targetStepId);

    const [removed] = steps.splice(draggedIndex, 1);
    steps.splice(targetIndex, 0, removed);

    setTestCase({ ...testCase, steps });
  };

  const handleDragEnd = () => {
    setDraggedStep(null);
  };

  const addAssertion = () => {
    if (!newAssertion.value) return;
    
    const assertion: Assertion = {
      id: `assertion-${Date.now()}`,
      type: newAssertion.type,
      value: newAssertion.value,
      description: newAssertion.description || `${newAssertion.type}: ${newAssertion.value}`,
    };
    
    setTestCase({
      ...testCase,
      assertions: [...testCase.assertions, assertion],
    });
    
    setNewAssertion({
      id: '',
      type: 'urlContains',
      value: '',
      description: '',
    });
    
    setShowAssertionDialog(false);
  };

  const deleteAssertion = (assertionId: string) => {
    setTestCase({
      ...testCase,
      assertions: testCase.assertions.filter((a) => a.id !== assertionId),
    });
  };

  const addVariable = () => {
    const key = prompt('Variable name:');
    if (!key) return;
    
    const value = prompt('Variable value:');
    if (value === null) return;
    
    setTestCase({
      ...testCase,
      variables: { ...testCase.variables, [key]: value },
    });
  };

  const updateVariable = (key: string, value: string) => {
    setTestCase({
      ...testCase,
      variables: { ...testCase.variables, [key]: value },
    });
  };

  const deleteVariable = (key: string) => {
    const newVariables = { ...testCase.variables };
    delete newVariables[key];
    setTestCase({ ...testCase, variables: newVariables });
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
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{t('cases.basicInfo')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">{t('cases.name')}</label>
              <Input
                value={testCase.name}
                onChange={(e) => setTestCase({ ...testCase, name: e.target.value })}
                placeholder={t('cases.namePlaceholder')}
              />
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
                {testCase.steps.map((step, index) => (
                  <div
                    key={step.id}
                    draggable
                    onDragStart={() => handleDragStart(step.id)}
                    onDragOver={(e) => handleDragOver(e, step.id)}
                    onDragEnd={handleDragEnd}
                    className={`border rounded-lg transition-all ${
                      draggedStep === step.id ? 'opacity-50' : ''
                    } ${!step.enabled ? 'opacity-50' : ''}`}
                  >
                    <div className="flex items-center p-3">
                      <GripVertical className="h-4 w-4 text-muted-foreground mr-2 cursor-move" />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="mr-2"
                        onClick={() => toggleStepExpanded(step.id)}
                      >
                        {expandedSteps.has(step.id) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </Button>
                      <span className="text-sm font-mono text-muted-foreground mr-2">
                        #{index + 1}
                      </span>
                      <Input
                        value={step.name}
                        onChange={(e) => updateStep(step.id, { name: e.target.value })}
                        className="flex-1"
                        placeholder={t('cases.stepNamePlaceholder')}
                      />
                      <Badge variant="outline" className="ml-2">
                        {step.action}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleStepEnabled(step.id)}
                        className="ml-2"
                      >
                        {step.enabled ? (
                          <Eye className="h-4 w-4" />
                        ) : (
                          <EyeOff className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteStep(step.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    {expandedSteps.has(step.id) && (
                      <div className="px-3 pb-3 space-y-3 border-t pt-3">
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
            <div className="flex items-center justify-between">
              <CardTitle>{t('cases.assertions')}</CardTitle>
              <Dialog open={showAssertionDialog} onOpenChange={setShowAssertionDialog}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    {t('cases.addAssertion')}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t('cases.addAssertion')}</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">{t('cases.type')}</label>
                      <Select
                        value={newAssertion.type}
                        onValueChange={(value) =>
                          setNewAssertion({ ...newAssertion, type: value })
                        }
                      >
                        <SelectTrigger>
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
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">{t('cases.value')}</label>
                      <Input
                        value={newAssertion.value}
                        onChange={(e) =>
                          setNewAssertion({ ...newAssertion, value: e.target.value })
                        }
                        placeholder={t('cases.assertionValuePlaceholder')}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">{t('cases.description')}</label>
                      <Input
                        value={newAssertion.description}
                        onChange={(e) =>
                          setNewAssertion({ ...newAssertion, description: e.target.value })
                        }
                        placeholder={t('cases.assertionDescriptionPlaceholder')}
                      />
                    </div>
                    <Button onClick={addAssertion} className="w-full">
                      {t('common.add')}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            {testCase.assertions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {t('cases.noAssertions')}
              </div>
            ) : (
              <div className="space-y-2">
                {testCase.assertions.map((assertion) => (
                  <div
                    key={assertion.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <Badge variant="outline">{assertion.type}</Badge>
                      <span className="text-sm">{assertion.description}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteAssertion(assertion.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{t('cases.variables')}</CardTitle>
              <Button size="sm" onClick={addVariable}>
                <Plus className="mr-2 h-4 w-4" />
                {t('cases.addVariable')}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {Object.keys(testCase.variables).length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {t('cases.noVariables')}
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(testCase.variables).map(([key, value]) => (
                  <div key={key} className="flex items-center space-x-2">
                    <Input
                      value={key}
                      onChange={(e) => {
                        const newVariables = { ...testCase.variables };
                        delete newVariables[key];
                        newVariables[e.target.value] = value;
                        setTestCase({ ...testCase, variables: newVariables });
                      }}
                      className="flex-1"
                      placeholder={t('cases.variableName')}
                    />
                    <span className="text-muted-foreground">=</span>
                    <Input
                      value={value}
                      onChange={(e) => updateVariable(key, e.target.value)}
                      className="flex-1"
                      placeholder={t('cases.variableValue')}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteVariable(key)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
