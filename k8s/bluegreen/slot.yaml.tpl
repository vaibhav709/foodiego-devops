# Practical 8 - slot template, rendered by Jenkins with envsubst (SLOT, IMAGE, RELEASE)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: foodiego-${SLOT}
  namespace: foodiego-bg
  labels: { app: foodiego, slot: "${SLOT}" }
  annotations: { foodiego/release: "${RELEASE}" }
spec:
  replicas: 3
  selector: { matchLabels: { app: foodiego, slot: "${SLOT}" } }
  template:
    metadata:
      labels: { app: foodiego, slot: "${SLOT}", release: "${RELEASE}" }
    spec:
      securityContext: { runAsNonRoot: true, runAsUser: 10001 }
      containers:
        - name: web
          image: ${IMAGE}
          env:
            - { name: SLOT_COLOR, value: "${SLOT}" }
            - { name: APP_VERSION, value: "${RELEASE}" }
          ports: [{ containerPort: 8000 }]
          readinessProbe: { httpGet: { path: /healthz, port: 8000 }, initialDelaySeconds: 3, periodSeconds: 4 }
          livenessProbe: { httpGet: { path: /healthz, port: 8000 }, initialDelaySeconds: 10, periodSeconds: 10 }
          resources:
            requests: { cpu: 50m, memory: 96Mi }
            limits: { cpu: 300m, memory: 192Mi }
