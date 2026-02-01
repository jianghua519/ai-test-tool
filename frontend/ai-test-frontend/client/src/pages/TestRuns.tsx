import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  PlayCircle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Loader2,
  ExternalLink
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import DashboardLayout from '@/components/DashboardLayout';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface TestRun {
  id: number;
  case_name: string;
  status: 'passed' | 'failed' | 'running' | 'pending';
  start_time: string;
  end_time: string;
}

export default function TestRuns() {
  const { t } = useTranslation();
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRuns();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchRuns = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/reports/runs`);
      if (response.ok) {
        const data = await response.json();
        setRuns(data);
      }
    } catch (error) {
      console.error('Failed to fetch runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'passed':
        return <Badge className="bg-chart-3 hover:bg-chart-3/80 text-white"><CheckCircle className="w-3 h-3 mr-1" /> {t('runs.passed')}</Badge>;
      case 'failed':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" /> {t('runs.failed')}</Badge>;
      case 'running':
        return <Badge variant="secondary" className="animate-pulse"><Loader2 className="w-3 h-3 mr-1 animate-spin" /> {t('runs.running')}</Badge>;
      default:
        return <Badge variant="outline">{t('runs.pending')}</Badge>;
    }
  };

  const calculateDuration = (start: string, end: string) => {
    if (!start || !end) return '-';
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    const diff = endTime - startTime;
    return `${(diff / 1000).toFixed(1)}s`;
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-display font-bold text-foreground">
            {t('common.testRuns')}
          </h1>
        </div>

        <div className="border rounded-lg bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">{t('runs.id')}</TableHead>
                <TableHead>{t('runs.caseName')}</TableHead>
                <TableHead>{t('common.status')}</TableHead>
                <TableHead>{t('runs.startTime')}</TableHead>
                <TableHead>{t('runs.duration')}</TableHead>
                <TableHead className="text-right">{t('common.actions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && runs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    {t('common.loading')}
                  </TableCell>
                </TableRow>
              ) : runs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    No test runs found
                  </TableCell>
                </TableRow>
              ) : (
                runs.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-mono text-muted-foreground">#{run.id}</TableCell>
                    <TableCell className="font-medium">
                      <div className="flex items-center">
                        <PlayCircle className="mr-2 h-4 w-4 text-primary" />
                        {run.case_name || 'Unknown Case'}
                      </div>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(run.status)}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {run.start_time ? new Date(run.start_time).toLocaleString() : '-'}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {calculateDuration(run.start_time, run.end_time)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" asChild>
                        <a href={`/runs/${run.id}`} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Report
                        </a>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </DashboardLayout>
  );
}
