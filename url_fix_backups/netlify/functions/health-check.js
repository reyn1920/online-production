// Health Check Serverless Function for TRAE AI
// Provides system health status for production monitoring

exports.handler = async (event, context) => {
  const startTime = Date.now();

  try {
    // Basic health checks
    const healthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'unknown',
      version: process.env.npm_package_version || '1.0.0',
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed/1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal/1024 / 1024),
        external: Math.round(process.memoryUsage().external/1024 / 1024),
      },
      responseTime: Date.now() - startTime,
      checks: {
        environment: process.env.NODE_ENV ? 'pass' : 'warn',
        secrets: process.env.TRAE_MASTER_KEY ? 'pass' : 'fail',
        dashboard: process.env.DASHBOARD_SECRET_KEY ? 'pass' : 'fail',
      },
    };

    // Determine overall health based on critical checks
    const criticalChecks = ['secrets', 'dashboard'];
    const failedCritical = criticalChecks.filter(check => healthStatus.checks[check] === 'fail');

    if (failedCritical.length > 0) {
      healthStatus.status = 'unhealthy';
      healthStatus.issues = failedCritical.map(check => `Critical check failed: ${check}`);
    }

    // Return appropriate HTTP status
    const httpStatus = healthStatus.status === 'healthy' ? 200 : 503;

    return {
      statusCode: httpStatus,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Health-Check': 'trae-ai-v1',
      },
      body: JSON.stringify(healthStatus, null, 2),
    };
  } catch (error) {
    console.error('Health check error:', error);

    return {
      statusCode: 503,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Health-Check': 'trae-ai-v1',
      },
      body: JSON.stringify(
        {
          status: 'error',
          timestamp: new Date().toISOString(),
          error: error.message,
          responseTime: Date.now() - startTime,
        },
        null,
        2
      ),
    };
  }
};
