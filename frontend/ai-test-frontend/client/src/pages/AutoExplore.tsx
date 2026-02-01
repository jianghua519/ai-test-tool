import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Play,
  Square,
  Loader2,
  Globe,
  FileText,
  Settings,
  CheckCircle,
  Target,
  Zap,
  Eye,
  ArrowRight
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
import DashboardLayout from '@/components/DashboardLayout';

interface BusinessAnalysis {
  key_features: string[];
  test_targets: string[];
  priority_areas: string[];
  exploration_strategy: string;
  confidence: 'high' | 'medium' | 'low';
}

interface ExploreProgress {
  status: 'idle' | 'analyzing' | 'exploring' | 'generating' | 'complete' | 'error';
  pages_explored: number;
  elements_found: number;
  cases_generated: number;
  current_url?: string;
  error?: string;
}

export default function AutoExplore() {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [maxDepth, setMaxDepth] = useState(3);
  const [maxPages, setMaxPages] = useState(20);
  const [analyzing, setAnalyzing] = useState(false);
  const [exploring, setExploring] = useState(false);
  const [analysis, setAnalysis] = useState<BusinessAnalysis | null>(null);
  const [progress, setProgress] = useState<ExploreProgress>({
    status: 'idle',
    pages_explored: 0,
    elements_found: 0,
    cases_generated: 0,
  });

  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const analyzeBusinessDescription = async () => {
    if (!description.trim()) return;
    if (!isValidUrl(url)) return;

    setAnalyzing(true);
    setProgress({ status: 'analyzing', pages_explored: 0, elements_found: 0, cases_generated: 0 });

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/ai/analyze-business`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url,
            description,
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        setAnalysis(result);
        setProgress({ ...progress, status: 'complete' });
      } else {
        setProgress({ ...progress, status: 'error', error: 'Analysis failed' });
      }
    } catch (error) {
      console.error('Failed to analyze:', error);
      setProgress({ ...progress, status: 'error', error: 'Analysis failed' });
    } finally {
      setAnalyzing(false);
    }
  };

  const startExploration = async () => {
    if (!analysis || !isValidUrl(url)) return;

    setExploring(true);
    setProgress({
      status: 'exploring',
      pages_explored: 0,
      elements_found: 0,
      cases_generated: 0,
    });

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/explore/start`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url,
            strategy: analysis.exploration_strategy,
            max_depth: maxDepth,
            max_pages: maxPages,
          }),
        }
      );

      if (response.ok) {
        const { explore_id } = await response.json();
        // Start polling for progress
        pollExplorationProgress(explore_id);
      } else {
        setProgress({ ...progress, status: 'error', error: 'Exploration failed' });
        setExploring(false);
      }
    } catch (error) {
      console.error('Failed to start exploration:', error);
      setProgress({ ...progress, status: 'error', error: 'Exploration failed' });
      setExploring(false);
    }
  };

  const stopExploration = () => {
    setExploring(false);
    setProgress({ ...progress, status: 'idle' });
  };

  const pollExplorationProgress = async (exploreId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/explore/${exploreId}`
        );
        if (response.ok) {
          const data = await response.json();
          setProgress({
            status: data.status,
            pages_explored: data.pages_explored,
            elements_found: data.elements_found,
            cases_generated: data.cases_generated,
            current_url: data.current_url,
          });

          if (data.status === 'complete' || data.status === 'error') {
            clearInterval(pollInterval);
            setExploring(false);
          }
        }
      } catch (error) {
        console.error('Failed to poll progress:', error);
      }
    }, 1000);

    // Auto-clear on component unmount
    return () => clearInterval(pollInterval);
  };

  const getConfidenceBadge = () => {
    if (!analysis) return null;
    const colors = {
      high: 'bg-green-500/10 text-green-600 border-green-500/20',
      medium: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
      low: 'bg-red-500/10 text-red-600 border-red-500/20',
    };
    return (
      <Badge className={colors[analysis.confidence]}>
        {analysis.confidence.toUpperCase()}
      </Badge>
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">
            {t('explore.title')}
          </h1>
          <p className="text-muted-foreground mt-2">
            Describe your business requirements and let AI explore and generate test cases
          </p>
        </div>

        {/* URL and Description Input */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              {t('explore.url')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={t('explore.urlPlaceholder')}
              className="font-mono"
            />
            {url && !isValidUrl(url) && (
              <p className="text-sm text-destructive">{t('explore.invalidUrl')}</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {t('explore.description')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('explore.descriptionPlaceholder')}
              rows={8}
              className="resize-none"
            />
            <div className="flex justify-between items-center">
              <div className="text-sm text-muted-foreground">
                {description.length} characters
              </div>
              <Button
                onClick={analyzeBusinessDescription}
                disabled={analyzing || !description.trim() || !isValidUrl(url)}
              >
                {analyzing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t('common.analyzing')}
                  </>
                ) : (
                  <>
                    <Zap className="mr-2 h-4 w-4" />
                    {t('explore.analyzingDescription')}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        {analysis && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-chart-3" />
                  {t('explore.strategyTitle')}
                </CardTitle>
                {getConfidenceBadge()}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4 text-chart-1" />
                  {t('explore.keyFeatures')}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {analysis.key_features.map((feature, index) => (
                    <Badge key={index} variant="outline" className="justify-start">
                      <CheckCircle className="mr-2 h-3 w-3 text-chart-3" />
                      {feature}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4 text-chart-2" />
                  {t('explore.testTargets')}
                </h4>
                <div className="space-y-2">
                  {analysis.test_targets.map((target, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-2 p-2 bg-muted/50 rounded"
                    >
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      {target}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-chart-4" />
                  {t('explore.priorityAreas')}
                </h4>
                <div className="space-y-2">
                  {analysis.priority_areas.map((area, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-chart-4/10 border border-chart-4/20 rounded"
                    >
                      <span className="text-sm">{area}</span>
                      <Eye className="h-4 w-4 text-chart-4" />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Exploration Settings */}
        {analysis && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                {t('explore.exploreSettings')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    {t('explore.maxDepth')}
                  </label>
                  <Select value={maxDepth.toString()} onValueChange={(v) => setMaxDepth(parseInt(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[1, 2, 3, 4, 5].map((d) => (
                        <SelectItem key={d} value={d.toString()}>
                          {d}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    {t('explore.maxPages')}
                  </label>
                  <Select value={maxPages.toString()} onValueChange={(v) => setMaxPages(parseInt(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[10, 20, 50, 100].map((p) => (
                        <SelectItem key={p} value={p.toString()}>
                          {p}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex gap-2">
                {!exploring ? (
                  <Button
                    onClick={startExploration}
                    disabled={!analysis}
                    className="flex-1"
                  >
                    <Play className="mr-2 h-4 w-4" />
                    {t('explore.startExplore')}
                  </Button>
                ) : (
                  <Button
                    onClick={stopExploration}
                    variant="destructive"
                    className="flex-1"
                  >
                    <Square className="mr-2 h-4 w-4" />
                    {t('explore.stopExplore')}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Exploration Progress */}
        {(exploring || progress.status === 'exploring' || progress.status === 'complete') && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                {t('explore.exploreProgress')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {progress.status === 'exploring' && (
                <div className="text-center py-4">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-chart-1" />
                  <p className="text-sm text-muted-foreground">{t('explore.exploringStatus')}</p>
                </div>
              )}

              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-chart-1">
                    {progress.pages_explored}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {t('explore.pagesExplored')}
                  </div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-chart-2">
                    {progress.elements_found}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {t('explore.elementsFound')}
                  </div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-chart-3">
                    {progress.cases_generated}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {t('explore.casesGenerated')}
                  </div>
                </div>
              </div>

              {progress.current_url && (
                <div className="text-sm text-muted-foreground font-mono bg-muted/50 p-2 rounded">
                  {progress.current_url}
                </div>
              )}

              {progress.status === 'complete' && (
                <Button className="w-full">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  {t('explore.generateCases')}
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
