on minimum(a, b)
	if a < b then
		return a
	end if
	return b
end minimum

on list_position(_item, _list)
	repeat with i from 1 to the count of _list
		if item i of _list = _item then
			return i
		end if
	end repeat
	return 0
end list_position

tell application "iTunes"
	set _playlist to current playlist
	set _id to id of current track
	set _ids to id of tracks of _playlist
	set _c to count of tracks of _playlist
end tell

set pos to list_position(_id, _ids) + 1
if pos = 1 or pos > _c then return ""
set _last to minimum(pos + 4, _c)

tell application "iTunes"
	set _list to get items pos thru _last of (get persistent ID of tracks of _playlist)
end tell

set text item delimiters to return
return _list as text
