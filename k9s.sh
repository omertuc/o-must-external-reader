#!/usr/bin/zsh

KUBECONFIG==(echo '
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: http://localhost:5000
  name: must-gather
contexts:
- context:
    cluster: must-gather
    user: must-gather
  name: must-gather
current-context: must-gather
preferences: {}
users:
- name: must-gather
  user:
    client-certificate: ''
    client-key: ''
') k9s
