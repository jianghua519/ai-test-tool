import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'wouter';
import { 
  Plus, 
  Search, 
  FileCode, 
  MoreVertical, 
  Play, 
  Edit, 
  Trash2,
  Bot
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
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

interface TestCase {
  id: number;
  name: string;
  description: string;
  steps: any[];
  updated_at: string;
}

export default function TestCases() {
  const { t } = useTranslation();
  const [cases, setCases] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/cases`);
      if (response.ok) {
        const data = await response.json();
        setCases(data);
      }
    } catch (error) {
      console.error('Failed to fetch cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCases = cases.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-3xl font-display font-bold text-foreground">
            {t('common.testCases')}
          </h1>
          <div className="flex gap-2">
            <Button variant="outline">
              <Bot className="mr-2 h-4 w-4" />
              {t('cases.generateAI')}
            </Button>
            <Link href="/cases/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                {t('cases.createTitle')}
              </Button>
            </Link>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder={t('common.search')}
              className="pl-8"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="border rounded-lg bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">ID</TableHead>
                <TableHead>{t('cases.name')}</TableHead>
                <TableHead>{t('cases.steps')}</TableHead>
                <TableHead className="hidden md:table-cell">{t('cases.description')}</TableHead>
                <TableHead className="text-right">{t('common.actions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    {t('common.loading')}
                  </TableCell>
                </TableRow>
              ) : filteredCases.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    {t('cases.noCases')}
                  </TableCell>
                </TableRow>
              ) : (
                filteredCases.map((testCase) => (
                  <TableRow key={testCase.id}>
                    <TableCell className="font-mono text-muted-foreground">#{testCase.id}</TableCell>
                    <TableCell className="font-medium">
                      <div className="flex items-center">
                        <FileCode className="mr-2 h-4 w-4 text-primary" />
                        {testCase.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="font-mono">
                        {testCase.steps?.length || 0} steps
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-muted-foreground truncate max-w-[200px]">
                      {testCase.description}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="icon" title={t('common.run')}>
                          <Play className="h-4 w-4 text-chart-3" />
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <Link href={`/cases/${testCase.id}`}>
                              <DropdownMenuItem>
                                <Edit className="mr-2 h-4 w-4" /> {t('common.edit')}
                              </DropdownMenuItem>
                            </Link>
                            <DropdownMenuItem className="text-destructive">
                              <Trash2 className="mr-2 h-4 w-4" /> {t('common.delete')}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
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
