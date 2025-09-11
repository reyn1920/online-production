# Trae AI Zero-Cost Monitoring Stack

A comprehensive, production-ready monitoring solution using open-source tools including Prometheus, Grafana, Alertmanager, and more. This stack provides complete observability for your Trae AI applications with zero licensing costs.

## 🚀 Quick Start

```bash
# Make the setup script executable
chmod +x setup_monitoring.sh

# Run the complete setup
./setup_monitoring.sh

# Or use individual commands
./setup_monitoring.sh start    # Start services
./setup_monitoring.sh status   # Check status
./setup_monitoring.sh logs     # View logs
```

## 📊 What's Included

### Core Monitoring Services
- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **Alertmanager** - Alert routing and notifications
- **Node Exporter** - System metrics
- **cAdvisor** - Container metrics
- **Blackbox Exporter** - External endpoint monitoring

### Supporting Services
- **Redis** - Caching and session storage
- **Nginx** - Reverse proxy and load balancing
- **Loki** - Log aggregation
- **Promtail** - Log collection
- **Jaeger** - Distributed tracing

### Custom Components
- **Zero Cost Monitoring Stack** - Custom Python monitoring service
- **Enhanced Web Scraping Tools** - Advanced scraping with monitoring
- **API Discovery Engine** - Automated API discovery and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │────│      Nginx      │────│     Grafana     │
│   (Port 8000)   │    │   (Port 80)     │    │   (Port 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Prometheus    │──────────────┘
                        │   (Port 9090)   │
                        └─────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Alertmanager   │    │ Node Exporter   │    │    cAdvisor     │
│   (Port 9093)   │    │   (Port 9100)   │    │   (Port 8080)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration Files

| File | Purpose | Description |
|------|---------|-------------|
| `docker-compose.monitoring.yml` | Container orchestration | Defines all services and their configurations |
| `prometheus.yml` | Prometheus config | Scrape targets, rules, and alerting |
| `alert_rules.yml` | Alert definitions | Prometheus alerting rules |
| `alertmanager.yml` | Alert routing | How alerts are sent and to whom |
| `grafana_dashboard.json` | Dashboard config | Pre-built Grafana dashboard |
| `monitoring_config.yaml` | Global settings | Environment-specific configurations |
| `.env` | Environment variables | Secrets and runtime configuration |

## 📈 Metrics and Monitoring

### System Metrics
- CPU usage, memory consumption, disk I/O
- Network traffic and connection states
- Container resource utilization
- Process and service health

### Application Metrics
- HTTP request rates, latency, and error rates
- Database connection pools and query performance
- Cache hit rates and memory usage
- Custom business metrics

### Web Scraping Metrics
- Scraping success/failure rates
- Response times and data quality
- Rate limiting and proxy usage
- Content extraction accuracy

### API Discovery Metrics
- API endpoint availability
- Authentication success rates
- Rate limit consumption
- Integration test results

## 🚨 Alerting

### Alert Categories

#### Critical Alerts (Immediate Response)
- Service down or unreachable
- High error rates (>5%)
- Memory usage >90%
- Disk space <10%

#### Warning Alerts (Monitor Closely)
- High response times (>2s)
- Memory usage >80%
- Disk space <20%
- Failed scraping attempts

#### Info Alerts (Awareness)
- New API endpoints discovered
- Configuration changes
- Scheduled maintenance

### Notification Channels
- **Email** - SMTP configuration for critical alerts
- **Slack** - Webhook integration for team notifications
- **Webhook** - Custom integrations for automation

## 🔐 Security Features

### Access Control
- Grafana authentication with configurable users
- Network isolation using Docker networks
- SSL/TLS encryption for external access
- Secret management via environment variables

### Data Protection
- Encrypted data transmission
- Secure credential storage
- Regular security scans
- Audit logging

## 📊 Dashboard Overview

The included Grafana dashboard provides:

### System Overview Panel
- Server uptime and load
- Memory and CPU utilization
- Network I/O statistics
- Disk usage trends

### Application Metrics Panel
- Request rate and response times
- Error rate tracking
- Database performance
- Cache efficiency

### Web Scraping Panel
- Scraping job status
- Success/failure rates
- Data quality metrics
- Performance trends

### API Discovery Panel
- Discovered APIs count
- Integration success rates
- Authentication status
- Rate limit monitoring

## 🛠️ Management Commands

### Service Management
```bash
# Start all services
./setup_monitoring.sh start

# Stop all services
./setup_monitoring.sh stop

# Restart services
./setup_monitoring.sh restart

# Check service status
./setup_monitoring.sh status
```

### Monitoring and Debugging
```bash
# View all logs
./setup_monitoring.sh logs

# View specific service logs
./setup_monitoring.sh logs prometheus
./setup_monitoring.sh logs grafana

# Run health checks
./setup_monitoring.sh health
```

### Data Management
```bash
# Create backup
./setup_monitoring.sh backup

# Clean all data (destructive)
./setup_monitoring.sh clean
```

## 🔧 Customization

### Adding Custom Metrics

1. **Application Metrics**: Add Prometheus client to your application
```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('app_request_duration_seconds', 'Request latency')

# Use in your application
REQUEST_COUNT.inc()
with REQUEST_LATENCY.time():
    # Your application logic
    pass
```

2. **Custom Scrape Targets**: Edit `prometheus.yml`
```yaml
scrape_configs:
  - job_name: 'my-custom-app'
    static_configs:
      - targets: ['localhost:8080']
    scrape_interval: 15s
```

### Adding Custom Alerts

Edit `alert_rules.yml`:
```yaml
groups:
  - name: custom_alerts
    rules:
      - alert: CustomMetricHigh
        expr: my_custom_metric > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Custom metric is high"
```

### Custom Dashboard Panels

1. Access Grafana at http://localhost:3000
2. Login with admin/admin123
3. Create new dashboard or edit existing
4. Add panels with PromQL queries

## 🌐 Access URLs

Once running, access these services:

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana Dashboard | http://localhost:3000 | admin/admin123 |
| Prometheus | http://localhost:9090 | None |
| Alertmanager | http://localhost:9093 | None |
| Node Exporter | http://localhost:9100 | None |
| cAdvisor | http://localhost:8080 | None |
| Jaeger Tracing | http://localhost:16686 | None |
| Application | http://localhost:8000 | Varies |

## 🔍 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
docker info

# Check port conflicts
netstat -tulpn | grep :3000

# View service logs
docker-compose -f docker-compose.monitoring.yml logs [service]
```

#### Metrics Not Appearing
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify scrape configuration in `prometheus.yml`
3. Check application metrics endpoint
4. Review Prometheus logs for errors

#### Alerts Not Firing
1. Check alert rules syntax: http://localhost:9090/rules
2. Verify Alertmanager configuration
3. Test notification channels
4. Check alert rule evaluation

#### Dashboard Issues
1. Verify Grafana datasource configuration
2. Check PromQL query syntax
3. Ensure metrics are being collected
4. Review Grafana logs

### Performance Optimization

#### High Memory Usage
```bash
# Adjust Prometheus retention
# Edit docker-compose.monitoring.yml
--storage.tsdb.retention.time=7d

# Reduce scrape frequency
# Edit prometheus.yml
scrape_interval: 30s
```

#### Slow Queries
```bash
# Enable query logging
# Add to prometheus.yml
global:
  query_log_file: /prometheus/query.log
```

## 📚 Advanced Configuration

### High Availability Setup

For production environments, consider:

1. **Prometheus HA**: Run multiple Prometheus instances
2. **Grafana HA**: Use external database (PostgreSQL)
3. **Alertmanager Clustering**: Configure multiple Alertmanager instances
4. **Load Balancing**: Use external load balancer

### External Storage

For long-term storage:

1. **Remote Write**: Configure Prometheus remote write
2. **S3 Storage**: Use Thanos or Cortex for object storage
3. **Database**: External PostgreSQL for Grafana

### Security Hardening

1. **TLS Encryption**: Enable HTTPS for all services
2. **Authentication**: Integrate with LDAP/OAuth
3. **Network Security**: Use VPN or private networks
4. **Regular Updates**: Keep all components updated

## 🤝 Contributing

To contribute to this monitoring stack:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd monitoring-stack

# Make changes
vim prometheus.yml

# Test changes
./setup_monitoring.sh restart
./setup_monitoring.sh health
```

## 📄 License

This monitoring stack uses open-source components:

- Prometheus: Apache License 2.0
- Grafana: AGPL v3
- Alertmanager: Apache License 2.0
- Node Exporter: Apache License 2.0
- Redis: BSD License

## 🆘 Support

For support and questions:

1. Check the troubleshooting section
2. Review service logs
3. Consult official documentation:
   - [Prometheus](https://prometheus.io/docs/)
   - [Grafana](https://grafana.com/docs/)
   - [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks

1. **Update Docker Images**: Monthly
```bash
docker-compose -f docker-compose.monitoring.yml pull
./setup_monitoring.sh restart
```

2. **Backup Data**: Weekly
```bash
./setup_monitoring.sh backup
```

3. **Review Alerts**: Monthly
4. **Update Dashboards**: As needed
5. **Security Patches**: As available

### Version Compatibility

| Component | Minimum Version | Recommended |
|-----------|----------------|-------------|
| Docker | 20.10+ | Latest |
| Docker Compose | 1.29+ | Latest |
| Prometheus | 2.30+ | Latest |
| Grafana | 8.0+ | Latest |

---

**Built with ❤️ for the Trae AI ecosystem**

This monitoring stack provides enterprise-grade observability at zero cost, enabling you to monitor, alert, and optimize your Trae AI applications with confidence.