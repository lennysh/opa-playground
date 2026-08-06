package aap_policy_examples

# Find credentials with no organization
violating_credentials := {cred.name | cred := input.credentials[_]; cred.organization == null}

default global_credential_allowed_false := {
	"allowed": true,
	"violations": [],
}

# If any credential is violating, deny access and return violations
global_credential_allowed_false := {
	"allowed": false,
	"violations": [sprintf("Credential used in job execution does not belong to any org. Violating credentials: [%s]", [concat(", ", violating_credentials)])],
} if {
	count(violating_credentials) > 0
}
