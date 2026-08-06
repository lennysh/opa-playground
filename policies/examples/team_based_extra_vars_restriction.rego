package aap_policy_examples

import rego.v1

# Define allowed values for specific keys in extra_vars based on teams
valid_extra_var_values_by_team := {
	"dev_team": {"environment": ["dev", "staging"]},
	"prod_team": {"environment": ["prod", "staging"]},
}

# Default response allowing extra_vars unless violations occur
default team_based_extra_vars_restriction := {
	"allowed": true,
	"violations": [],
}

# Evaluate extra_vars against allowed values considering team memberships
team_based_extra_vars_restriction := result if {
	# Extract extra_vars from input
	input_extra_vars := object.get(input, ["extra_vars"], {})

	# Extract user's team names
	user_teams := {team | team := input.created_by.teams[_].name}

	violating_keys := [key |
		allowed_vals := allowed_values_for_key_and_teams(key, user_teams)
		input_value := input_extra_vars[key]
		allowed_values_for_key_and_teams(key, user_teams)
		not allowed_value(input_value, allowed_vals)
	]

	count(violating_keys) > 0

	result := {
		"allowed": false,
		"violations": [sprintf("extra_vars contain disallowed values for keys: %v. Allowed extra_vars for your teams (%v): %v", [violating_keys, user_teams, allowed_values_for_user_teams(user_teams)])],
	}
}

# Retrieve allowed values for a specific key based on user's teams
allowed_values_for_key_and_teams(key, teams) := values if {
	values := {val | team := teams[_]; val := valid_extra_var_values_by_team[team][key][_]; valid_extra_var_values_by_team[team][key]}
}

# Retrieve all allowed values based on user's teams
allowed_values_for_user_teams(teams) := team_values if {
	team_values := {team: valid_extra_var_values_by_team[team] | team := teams[_]; valid_extra_var_values_by_team[team]}
}

# Check if given value is in allowed values set
allowed_value(value, allowed_values) if {
	allowed_values[_] == value
}
