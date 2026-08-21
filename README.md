# OPA Playground

Rego policies for Ansible Automation Platform (AAP) Policy as Code, served by the OPA instance on OpenShift (`aap-opa`).

Policies are published as a ConfigMap (`opa-policies`) via Argo CD. The OPA Deployment mounts that ConfigMap at `/policies` with `--watch`.

## Layout

```text
policies/                 # Rego modules (any subfolders)
kustomization.yaml        # Builds ConfigMap opa-policies for Argo CD
scripts/sync-kustomization-files.py
```

Example policies under `policies/aap/aap_policy_examples/` are from [ansible/example-opa-policy-for-aap](https://github.com/ansible/example-opa-policy-for-aap/tree/main/aap_policy_examples).

## Query paths

AAP associates a policy query path such as:

```text
aap_policy_examples/<rule_name>
```

Examples: `aap_policy_examples/jt_naming_validation`, `aap_policy_examples/maintenance_window`.

Some example rules always deny (`allowed_false`, `superuser_allowed_false`, …). Only associate those when you intend to test denials.

## Local checks

```bash
# List modules after Argo sync / OPA reload
curl -s http://opa-aap-opa.apps.ocp001.lennysh.net/v1/policies | jq .

# Evaluate a rule (replace input as needed)
curl -s http://opa-aap-opa.apps.ocp001.lennysh.net/v1/data/aap_policy_examples/jt_naming_validation \
  -H 'Content-Type: application/json' \
  -d '{"input":{}}' | jq .
```

## Updating policies

1. Edit or add `.rego` files anywhere under `policies/` (nested folders are fine).
2. Refresh the ConfigMap file list:

   ```bash
   ./scripts/sync-kustomization-files.py
   ```

   Useful flags: `-n` / `--dry-run` (preview), `-c` / `--check` (CI-style fail if stale). Basenames must be unique (ConfigMap keys use the filename only).
3. Commit and push to `main`; Argo CD syncs the ConfigMap; OPA reloads via `--watch`.

### Pre-commit hook

Install once (requires [pre-commit](https://pre-commit.com)):

```bash
pip install pre-commit   # or: dnf install pre-commit
pre-commit install
```

On commit, the hook runs `scripts/sync-kustomization-files.py --fail-on-change`. If `kustomization.yaml` was missing any `.rego` files, it updates the file and **fails the commit** so you can stage it and commit again:

```bash
git add kustomization.yaml
git commit
```

## Related repos

- [cheat-sheets](https://github.com/lennysh/cheat-sheets) — copy-paste notes (AAP, Automation Orchestrator, OpenShift, …)
- [argocd-playground](https://github.com/lennysh/argocd-playground) — Argo CD GitOps for AAP, Automation Orchestrator, and related apps on OpenShift
