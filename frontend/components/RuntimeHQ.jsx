import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Activity,
  Database,
  HardDrive,
  Cpu,
  Memory,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  Users,
  FileText,
  DollarSign,
  Clock,
  Play,
  Pause,
  Square
} from 'lucide-react';

const RuntimeHQ = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [revenueData, setRevenueData] = useState(null);
  const [queueStats, setQueueStats] = useState(null);
  const [proofStats, setProofStats] = useState(null);

  // Fetch system status
  const fetchSystemStatus = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/runtimehq/health');
      if (!response.ok) throw new Error('Failed to fetch system status');
      const data = await response.json();
      setSystemStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  };

  // Fetch revenue data
  const fetchRevenueData = async () => {
    try {
      const response = await fetch('/api/runtimehq/revenue/summary');
      if (!response.ok) throw new Error('Failed to fetch revenue data');
      const data = await response.json();
      setRevenueData(data);
    } catch (err) {
      console.error('Failed to fetch revenue data:', err);
    }
  };

  // Fetch queue statistics
  const fetchQueueStats = async () => {
    try {
      const response = await fetch('/api/runtimehq/queue/stats');
      if (!response.ok) throw new Error('Failed to fetch queue stats');
      const data = await response.json();
      setQueueStats(data);
    } catch (err) {
      console.error('Failed to fetch queue stats:', err);
    }
  };

  // Fetch proof statistics
  const fetchProofStats = async () => {
    try {
      const response = await fetch('/api/runtimehq/proofs/stats');
      if (!response.ok) throw new Error('Failed to fetch proof stats');
      const data = await response.json();
      setProofStats(data);
    } catch (err) {
      console.error('Failed to fetch proof stats:', err);
    }
  };

  // Run database migration
  const runMigration = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/runtimehq/migrate', { method: 'POST' });
      if (!response.ok) throw new Error('Migration failed');
      await fetchSystemStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshing(false);
    }
  };

  // Queue management functions
  const pauseQueue = async () => {
    try {
      await fetch('/api/runtimehq/queue/pause', { method: 'POST' });
      await fetchQueueStats();
    } catch (err) {
      console.error('Failed to pause queue:', err);
    }
  };

  const resumeQueue = async () => {
    try {
      await fetch('/api/runtimehq/queue/resume', { method: 'POST' });
      await fetchQueueStats();
    } catch (err) {
      console.error('Failed to resume queue:', err);
    }
  };

  const clearQueue = async () => {
    if (!confirm('Are you sure you want to clear all pending jobs?')) return;
    try {
      await fetch('/api/runtimehq/queue/clear', { method: 'POST' });
      await fetchQueueStats();
    } catch (err) {
      console.error('Failed to clear queue:', err);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    fetchRevenueData();
    fetchQueueStats();
    fetchProofStats();

    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchQueueStats();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'ok':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'error':
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'ok':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
      case 'critical':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading RuntimeHQ Dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">RuntimeHQ Dashboard</h1>
          <p className="text-muted-foreground">
            System monitoring and management for your production environment
          </p>
        </div>
        <Button
          onClick={fetchSystemStatus}
          disabled={refreshing}
          variant="outline"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* System Status Overview */}
      {systemStatus && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Status</CardTitle>
              {getStatusIcon(systemStatus.overall_status)}
            </CardHeader>
            <CardContent>
              <Badge className={getStatusColor(systemStatus.overall_status)}>
                {systemStatus.overall_status?.toUpperCase()}
              </Badge>
              <p className="text-xs text-muted-foreground mt-2">
                Last checked: {new Date(systemStatus.timestamp).toLocaleTimeString()}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Database</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <Badge className={getStatusColor(systemStatus.checks?.database?.status)}>
                {systemStatus.checks?.database?.status?.toUpperCase()}
              </Badge>
              <p className="text-xs text-muted-foreground mt-2">
                {systemStatus.checks?.database?.message}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disk Space</CardTitle>
              <HardDrive className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {systemStatus.checks?.disk_space?.usage_percent}%
              </div>
              <Progress
                value={systemStatus.checks?.disk_space?.usage_percent || 0}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground mt-2">
                {systemStatus.checks?.disk_space?.free_gb}GB free
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory</CardTitle>
              <Memory className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {systemStatus.checks?.memory?.usage_percent}%
              </div>
              <Progress
                value={systemStatus.checks?.memory?.usage_percent || 0}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground mt-2">
                {systemStatus.checks?.memory?.available_gb}GB available
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="queue">Job Queue</TabsTrigger>
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
          <TabsTrigger value="proofs">Visual Proofs</TabsTrigger>
          <TabsTrigger value="system">System Details</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {revenueData && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">${revenueData.total_revenue}</div>
                  <p className="text-xs text-muted-foreground">
                    {revenueData.total_transactions} transactions
                  </p>
                </CardContent>
              </Card>
            )}

            {queueStats && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Queue Status</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{queueStats.pending_jobs}</div>
                  <p className="text-xs text-muted-foreground">
                    {queueStats.running_jobs} running, {queueStats.completed_jobs} completed
                  </p>
                </CardContent>
              </Card>
            )}

            {proofStats && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Visual Proofs</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{proofStats.total_proofs}</div>
                  <p className="text-xs text-muted-foreground">
                    {proofStats.total_size_mb}MB total
                  </p>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Uptime</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">99.9%</div>
                <p className="text-xs text-muted-foreground">
                  Last 30 days
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Queue Management Tab */}
        <TabsContent value="queue" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Job Queue Management</h3>
            <div className="flex gap-2">
              <Button onClick={pauseQueue} variant="outline" size="sm">
                <Pause className="h-4 w-4 mr-2" />
                Pause
              </Button>
              <Button onClick={resumeQueue} variant="outline" size="sm">
                <Play className="h-4 w-4 mr-2" />
                Resume
              </Button>
              <Button onClick={clearQueue} variant="destructive" size="sm">
                <Square className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>

          {queueStats && (
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle>Pending Jobs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{queueStats.pending_jobs}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Running Jobs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{queueStats.running_jobs}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Completed Jobs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{queueStats.completed_jobs}</div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Revenue Tab */}
        <TabsContent value="revenue" className="space-y-4">
          <h3 className="text-lg font-medium">Revenue Analytics</h3>
          {revenueData && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Revenue Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span>Total Revenue:</span>
                    <span className="font-bold">${revenueData.total_revenue}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Transactions:</span>
                    <span>{revenueData.total_transactions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Transaction:</span>
                    <span>${revenueData.average_transaction}</span>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Revenue tracking and analytics will be displayed here.
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Proofs Tab */}
        <TabsContent value="proofs" className="space-y-4">
          <h3 className="text-lg font-medium">Visual Proof Management</h3>
          {proofStats && (
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle>Total Proofs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{proofStats.total_proofs}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Storage Used</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{proofStats.total_size_mb}MB</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Recent Uploads</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{proofStats.recent_uploads || 0}</div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* System Details Tab */}
        <TabsContent value="system" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">System Details</h3>
            <Button onClick={runMigration} disabled={refreshing}>
              <Database className="h-4 w-4 mr-2" />
              Run Migration
            </Button>
          </div>

          {systemStatus && (
            <div className="grid gap-4">
              {Object.entries(systemStatus.checks || {}).map(([key, check]) => (
                <Card key={key}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {getStatusIcon(check.status)}
                      {key.replace('_', ' ').toUpperCase()}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Badge className={getStatusColor(check.status)}>
                      {check.status?.toUpperCase()}
                    </Badge>
                    <p className="text-sm mt-2">{check.message}</p>
                    {check.details && (
                      <pre className="text-xs mt-2 p-2 bg-gray-100 rounded overflow-auto">
                        {JSON.stringify(check.details, null, 2)}
                      </pre>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RuntimeHQ;
