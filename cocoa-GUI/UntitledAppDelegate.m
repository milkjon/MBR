//
//  UntitledAppDelegate.m
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import "UntitledAppDelegate.h"
#import "MBTune.h"

#define kTunes @"tunes"

@implementation UntitledAppDelegate


- (void)applicationDidFinishLaunching:(NSNotification *)aNotification 
{
	NSLog(@"didFinishLaunching");
	
	[tableView setDoubleAction: @selector(addToiTunesPlaylist:)];
	
	// Create two dummy objects and add them to the list
	MBTune* tune1 = [[[MBTune alloc] init] autorelease];
	[tune1 setTrackID: @"23746"];
	[tune1 setTitle: @"When Summer Comes"];
	[tune1 setArtist: @"Pepper"];
	[tune1 setLength: @"3:16"];
	[tune1 setRequester: @"John"];

	MBTune* tune2 = [[[MBTune alloc] init] autorelease];
	[tune2 setTrackID: @"9400"];
	[tune2 setTitle: @"Parachute"];
	[tune2 setArtist: @"Sean Lennon"];
	[tune2 setLength: @"3:19"];
	[tune2 setRequester: @"Paul"];	
	
	[self willChangeValueForKey: kTunes];
	[tunes addObject: tune1];
	[tunes addObject: tune2];
	[self didChangeValueForKey: kTunes];
}

- (IBAction) add: (id) sender
{
	NSLog(@"add");
	
	MBTune* tune = [[[MBTune alloc] init] autorelease];
	[tune setTitle: @"Lipsill"];
	[tune setArtist: @"Dungen"];
	[tune setRequestTime: [NSDate date]];
	
	[self willChangeValueForKey: kTunes];
	[tunes addObject: tune];	
	[self didChangeValueForKey: kTunes];
}

- (IBAction) addToiTunesPlaylist: (id) sender
{
	NSLog(@"addToiTunes");
	NSLog(@"%@", [arrayController selectedObjects]);
	
	MBTune* track = nil;
	
	if ([sender isKindOfClass: [NSTableView class]]) {
		int row = [tableView clickedRow];
		if (row == -1) 
			return;
		
		track = [[arrayController arrangedObjects] objectAtIndex: row];
	} else {
		track = [[arrayController selectedObjects] objectAtIndex: 0];	
	}
	
	if (! track) return;
	
	NSString *playlist = @"radio";
	NSString *trackID = [track trackID];
	
	NSString *source = [NSString stringWithFormat: 
		@"tell application \"iTunes\"\n"
		@"    set pl to some playlist whose name is \"Library\"\n"
		@"    set t to some track of pl whose database ID is %@ \n"
		@"    set target to some playlist whose name is \"%@\" \n"
		@"    add (get location of t) to target \n"
		@"end tell ", trackID, playlist]; 
						
	NSAppleScript *script = [[[NSAppleScript alloc] initWithSource: source] autorelease];
	
	NSDictionary* error = nil;
	[script executeAndReturnError: &error];
	
	if (error)
		NSLog(@"%@", error);	
}

- (id) init
{
	self = [super init];
	if (self != nil) {
		tunes = [[NSMutableArray alloc] init];
	}
	return self;
}

- (void) dealloc
{
	[tunes release];
	[super dealloc];
}


@end
