# OPA Playground

Rego policies for Ansible Automation Platform (AAP) Policy as Code, served by the OPA instance on OpenShift (`aap-opa`).

Policies are published as a ConfigMap (`opa-policies`) via Argo CD. The OPA Deployment mounts that ConfigMap at `/policies` with `--watch`.

## Layout

```text
policies/examples/  # Example Rego modules (package aap_policy_examples)
kustomization.yaml  # Builds ConfigMap opa-policies for Argo CD
```

Seeded from [ansible/example-opa-policy-for-aap](https://github.com/ansible/example-opa-policy-for-aap/tree/main/aap_policy_examples).

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

1. Edit or add `.rego` files under `policies/examples/` (or your own folder under `policies/`).
2. If you add a file, list it under `configMapGenerator` in `kustomization.yaml`.
3. Commit and push to `main`; Argo CD syncs the ConfigMap; OPA reloads via `--watch`.
