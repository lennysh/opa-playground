package aap_policy_examples

import rego.v1

allowed_false := {
	"allowed": false,
	"violations": ["No job execution is allowed"],
}
