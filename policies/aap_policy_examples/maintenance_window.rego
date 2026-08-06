package aap_policy_examples

# Define maintenance window in UTC
maintenance_start_hour := 12 # 12:00 UTC (5 PM EST)

maintenance_end_hour := 4 # 04:00 UTC (9 AM EST)

# Extract the job creation timestamp (which is in UTC)
created_clock := time.clock(time.parse_rfc3339_ns(input.created)) # returns [hour, minute, second]

created_hour_utc := created_clock[0]

# Check if job was created within the maintenance window (UTC)
is_maintenance_time if {
	created_hour_utc >= maintenance_start_hour # After 12:00 UTC
}

is_maintenance_time if {
	created_hour_utc <= maintenance_end_hour # Before or at 04:00 UTC
}

default maintenance_window := {
	"allowed": true,
	"violations": [],
}

maintenance_window := {
	"allowed": false,
	"violations": ["No job execution allowed outside of maintenance window"],
} if {
	not is_maintenance_time
}
