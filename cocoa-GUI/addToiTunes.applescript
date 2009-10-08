tell application "iTunes"
	set pl to some playlist whose name is "Library"
	set t to some track of pl whose persistent ID is "%@"
	set target to some playlist whose name is "%@"
	add (get location of t) to target
end tell