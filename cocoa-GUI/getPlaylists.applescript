set r to {}

tell application "iTunes"
	set x to every user playlist whose smart is not true
	repeat with l in x
		set n to name of l
		set r to r & n
	end repeat
end tell

set text item delimiters to return
return r as text