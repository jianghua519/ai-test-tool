import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  Play, 
  Clock,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/DashboardLayout';

interface TestRun {
  id: number;
  case_id: number;
  status: string;
  start_time: string;
  end_time: string;
  result?: any;
}

export default function Dashboard() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalCases: 0,
    totalRuns: 0,
    passRate: 0,
    systemStatus: 'Online'
  });
  const [recentRuns, setRecentRuns] = useState<TestRun[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000';
      
      const [casesResponse, runsResponse] = await Promise.all([
        fetch(`${apiUrl}/api/cases`),
        fetch(`${apiUrl}/api/exec/runs/recent`)
      ]);

      if (casesResponse.ok) {
        const cases = await casesResponse.json();
        setStats(prev => ({ ...prev, totalCases: cases.length || 0 }));
      }

      if (runsResponse.ok) {
        const runs = await runsResponse.json();
        setRecentRuns(runs || []);
        
        const passedCount = runs.filter((r: TestRun) => r.status === 'passed').length;
        const passRate = runs.length > 0 ? (passedCount / runs.length * 100).toFixed(1) : 0;
        
        setStats(prev => ({
          ...prev,
          totalRuns: runs.length || 0,
          passRate: `${passRate}%`
        }));
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timeString: string) => {
    const time = new Date(timeString);
    const now = new Date();
    const diff = Math.floor((now.getTime() - time.getTime()) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return time.toLocaleDateString();
  };

  const formatDuration = (startTime: string, endTime: string) => {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diff = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (diff < 60) return `${diff}s`;
    return `${Math.floor(diff / 60)}m ${diff % 60}s`;
  };

  const statsData = [
    { 
      title: t('dashboard.totalCases'), 
      value: stats.totalCases.toString(), 
      icon: Activity,
      color: 'text-primary'
    },
    { 
      title: t('dashboard.totalRuns'), 
      value: stats.totalRuns.toString(), 
      icon: Play,
      color: 'text-chart-2'
    },
    { 
      title: t('dashboard.passRate'), 
      value: stats.passRate, 
      icon: CheckCircle,
      color: 'text-chart-3'
    },
    { 
      title: t('dashboard.systemStatus'), 
      value: stats.systemStatus, 
      icon: Zap,
      color: 'text-chart-5'
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-display font-bold text-foreground">
          {t('common.dashboard')}
        </h1>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statsData.map((stat) => (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.recentRuns')}</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">
                {t('common.loading')}
              </div>
            ) : recentRuns.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {t('dashboard.noRecentRuns')}
              </div>
            ) : (
              <div className="space-y-4">
                {recentRuns.map((run) => (
                  <div key={run.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      {run.status === 'passed' ? (
                        <CheckCircle className="h-5 w-5 text-chart-3" />
                      ) : (
                        <XCircle className="h-5 w-5 text-destructive" />
                      )}
                      <div>
                        <div className="font-medium">Run #{run.id}</div>
                        <div className="text-sm text-muted-foreground">
                          {formatTime(run.start_time)}
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {run.end_time ? formatDuration(run.start_time, run.end_time) : 'Running...'}
                    </div>
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
