package aap_policy_examples

import rego.v1

default superuser_allowed_false := {
	"allowed": true,
	"violations": [],
}

superuser_allowed_false := {
	"allowed": false,
	"violations": ["SuperUser is not allow to launch jobs"],
} if {
	input.created_by.is_superuser
}
