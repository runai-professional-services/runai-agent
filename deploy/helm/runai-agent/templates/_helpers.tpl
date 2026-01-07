{{/*
Expand the name of the chart.
*/}}
{{- define "runai-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "runai-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "runai-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "runai-agent.labels" -}}
helm.sh/chart: {{ include "runai-agent.chart" . }}
{{ include "runai-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "runai-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "runai-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Agent namespace - centralized namespace for the agent deployment
*/}}
{{- define "runai-agent.namespace" -}}
{{- .Values.global.namespace | default "runai-agent" }}
{{- end }}

{{/*
Get Run:AI client ID from secret or values
*/}}
{{- define "runai-agent.clientId" -}}
{{- if .Values.runai.existingSecret }}
{{- printf "valueFrom:\n  secretKeyRef:\n    name: %s\n    key: RUNAI_CLIENT_ID" .Values.runai.existingSecret | nindent 10 }}
{{- else }}
{{- .Values.runai.clientId }}
{{- end }}
{{- end }}

{{/*
PVC name for failure analysis
*/}}
{{- define "runai-agent.pvcName" -}}
{{- if .Values.failureAnalysis.persistence.existingClaim }}
{{- .Values.failureAnalysis.persistence.existingClaim }}
{{- else }}
{{- printf "%s-failure-db" (include "runai-agent.fullname" .) }}
{{- end }}
{{- end }}

