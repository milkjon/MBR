//
//  UntitledAppDelegate.m
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import "MBRAppDelegate.h"
#import "MBTune.h"

#define kRequests @"requests"

@implementation MBRAppDelegate


- (void)applicationDidFinishLaunching:(NSNotification *)aNotification 
{
	NSLog(@"didFinishLaunching");
	
	[tableView setDoubleAction: @selector(addToiTunesPlaylist:)];
	
	// Create two dummy objects and add them to the list
	MBTune *tune1 = [[[MBTune alloc] init] autorelease];
	[tune1 setTrackID: @"23746"];
	[tune1 setTitle: @"When Summer Comes"];
	[tune1 setArtist: @"Pepper"];
	[tune1 setLength: @"3:16"];
	[tune1 setRequester: @"John"];

	MBTune *tune2 = [[[MBTune alloc] init] autorelease];
	[tune2 setTrackID: @"9400"];
	[tune2 setTitle: @"Parachute"];
	[tune2 setArtist: @"Sean Lennon"];
	[tune2 setLength: @"3:19"];
	[tune2 setRequester: @"Paul"];	
	
	[self willChangeValueForKey: kRequests];
	[requests addObject: tune1];
	[requests addObject: tune2];
	[self didChangeValueForKey: kRequests];
}

- (IBAction) add: (id) sender
{
	NSLog(@"add");
	
	MBTune *tune = [[[MBTune alloc] init] autorelease];
	[tune setTitle: @"Lipsill"];
	[tune setArtist: @"Dungen"];
	[tune setRequestTime: [NSDate date]];
	
	[self willChangeValueForKey: kRequests];
	[requests addObject: tune];	
	[self didChangeValueForKey: kRequests];
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
	
	NSDictionary *error = nil;
	[script executeAndReturnError: &error];
	
	if (error)
		NSLog(@"%@", error);	
}

- (void) checkRequests
{
	// FIXME: Implementation missing
	//     - Check if this could be done via stdout or something
	
	// Read the file
	// Add new requests to the array.
	
	NSLog(@"check requests");
}

- (void) querySong
{
	NSString *source = @"tell application \"iTunes\" to get persistent id of current track";
	NSAppleScript* script = [[[NSAppleScript alloc] initWithSource: source] autorelease];
	NSString *ident = [[script executeAndReturnError: nil] stringValue];
	NSLog(@"persistent identifer: %@", ident);
	
	// Make the http request
	NSString *str = [NSString stringWithFormat: @"http://localhost:15800/now-playing?songid=%@", ident];
	NSString *result = [NSString stringWithContentsOfURL: [NSURL URLWithString: str]];
}

- (id) init
{
	self = [super init];
	if (self != nil) {
		requests = [[NSMutableArray alloc] init];
		requestCheckTimer_ = [NSTimer scheduledTimerWithTimeInterval: 10 target: self selector: @selector(checkRequests) userInfo: nil repeats: YES];
		songQueryTimer_ = [NSTimer scheduledTimerWithTimeInterval: 5 target: self selector: @selector(querySong) userInfo: nil repeats: YES];

	}
	return self;
}

- (void) dealloc
{
	[requests release];
	[requestCheckTimer_ invalidate];
	[requestCheckTimer_ release];
	[songQueryTimer_ invalidate];
	[songQueryTimer_ release];
	[super dealloc];
}


@end
