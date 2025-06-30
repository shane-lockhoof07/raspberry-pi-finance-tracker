# Personal Finance Tracker - Raspberry Pi Kubernetes Deployment

## 🎯 Project Overview

A complete personal finance tracking system deployed on Raspberry Pi using modern DevOps practices. This project demonstrates expertise in containerization, Kubernetes orchestration, full-stack development, and infrastructure automation.

## 🚀 Key Technologies

- **Frontend**: Vue.js 3 + Vuetify (Material Design)
- **Backend**: FastAPI (Python) with PostgreSQL
- **Infrastructure**: Kubernetes (K3s) on Raspberry Pi
- **Containerization**: Docker with multi-stage builds
- **DevOps**: CI/CD with GitHub Actions, automated deployments
- **Security**: Kubernetes secrets, RBAC, network policies
- **Monitoring**: Health checks, logging, automated backups

## 🏗️ Architecture

```
┌────────────────────────┐    ┌─────────────────┐
│   Finance Website      │    │                 │
│  ┌─────────┬─────────┐ │    │  Home Assistant │
│  │Frontend │ Backend │ │    │   (Optional)    │
│  └─────────┴─────────┘ │    └─────────────────┘
└───────────┬────────────┘           │
            │                        │
            ▼                        ▼
┌─────────────────────────────────────────────────┐
│                K3s Cluster                      │
├─────────────────────────────────────────────────┤
│  ┌───────────┐   ┌─────────────────────────┐    │
│  │PostgreSQL │   │ Transaction Processor   │    │
│  └───────────┘   └─────────────────────────┘    │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Persistent Storage                 │
├─────────────────────────────────────────────────┤
│  ┌───────────┐   ┌───────────┐   ┌───────────┐  │
│  │Reference  │   │Transaction│   │PostgreSQL │  │
│  │   Data    │   │   Data    │   │   Data    │  │
│  └───────────┘   └───────────┘   └───────────┘  │
└─────────────────────────────────────────────────┘
```

## 💡 Technical Highlights

### **Kubernetes Infrastructure**
- **Multi-namespace architecture** for security isolation
- **Persistent volumes** for data persistence
- **Network policies** for micro-segmentation
- **Resource limits** and health checks
- **Horizontal Pod Autoscaling** ready

### **DevOps & Automation**
- **GitOps workflow** with automated deployments
- **Multi-stage Docker builds** for optimization
- **Database migration scripts** with rollback support
- **Automated backup system** with email notifications
- **Infrastructure as Code** - all configs in version control

### **Application Features**
- **RESTful API** with OpenAPI documentation
- **Responsive UI** with modern Material Design
- **Real-time transaction processing** from CSV imports
- **Categorization engine** with machine learning potential
- **Budget tracking** and spending analytics
- **Net worth monitoring** over time

## 🔧 Development Workflow

### **Local Development**
```bash
# API Development
cd finances-website/finances-api
poetry install
poetry run uvicorn main:app --reload

# Frontend Development  
cd finances-website/finances-ui
npm install
npm run dev
```

### **Container Builds**
```bash
# Build and push API
docker build -t localhost:32000/finances-api:latest ./finances-website/finances-api
docker push localhost:32000/finances-api:latest

# Build and push UI
docker build -t localhost:32000/finances-ui:latest ./finances-website/finances-ui
docker push localhost:32000/finances-ui:latest
```

### **Kubernetes Deployment**
```bash
# Apply all configurations
kubectl apply -f k8s/namespaces/
kubectl apply -f k8s/postgres_db/
kubectl apply -f k8s/finances_website/
kubectl apply -f k8s/ingress/

# Rolling updates
kubectl rollout restart deployment/finances-api -n finances-app
kubectl rollout restart deployment/finances-ui -n finances-app
```

## 📊 Monitoring & Observability

- **Health check endpoints** for all services
- **Structured logging** with correlation IDs
- **Database connection monitoring**
- **Resource utilization tracking**
- **Automated backup verification**

## 🔒 Security Features

- **Kubernetes RBAC** for service accounts
- **Network policies** for traffic segmentation
- **Secret management** with base64 encoding
- **Non-root container execution**
- **Regular security updates** via automation

## 🚀 Deployment Options

This project supports multiple deployment scenarios:

1. **Single Raspberry Pi** (demonstrated)
2. **Multi-node Raspberry Pi cluster**
3. **Cloud Kubernetes** (EKS, GKE, AKS)
4. **Local development** with Docker Compose

## 📈 Scalability Considerations

- **Stateless application design** for horizontal scaling
- **Database connection pooling** for performance
- **Container resource limits** for predictable behavior
- **Load balancing** ready with multiple replicas
- **Caching layer** implementation ready

## 🔮 Future Enhancements

- **Machine learning** for transaction categorization
- **Mobile app** with React Native
- **Real-time notifications** with WebSockets
- **Advanced analytics** with time-series data
- **Integration APIs** for banks and financial services

## 📋 Setup Instructions

### Prerequisites
- Raspberry Pi 4+ (4GB RAM minimum)
- 32GB+ storage (SSD recommended)
- Kubernetes cluster (K3s)
- Docker registry access

### Quick Start
```bash
# Clone the repository
git clone https://github.com/your-username/raspberry-pi-finance.git
cd raspberry-pi-finance

# Create secrets (see secrets.example.yaml)
kubectl apply -f k8s/postgres_db/secrets.yaml

# Deploy the application
kubectl apply -f k8s/
```

For detailed setup instructions, see [SETUP.md](SETUP.md)

## 🤝 Contributing

This is a portfolio project, but I welcome discussions about architecture decisions and potential improvements. Feel free to open issues for questions or suggestions.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 💼 About This Project

This project showcases my experience with:
- **Cloud-native application development**
- **Kubernetes orchestration and management**
- **DevOps practices and CI/CD pipelines**
- **Full-stack web development**
- **Infrastructure as Code**
- **Database design and management**
- **Security best practices**

Built as part of my journey in cloud engineering and DevOps, demonstrating practical skills in modern infrastructure management and application deployment.