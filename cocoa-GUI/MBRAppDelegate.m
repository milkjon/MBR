//
//  UntitledAppDelegate.m
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

// TODO : http requests off main thread

#import "MBRAppDelegate.h"
#import "MBTune.h"

#define kRequests @"requests"

#define BASEURL @"http://localhost:15800/"
#define PYTHON  @"/usr/bin/python"

@implementation MBRAppDelegate

#pragma mark talking to webserver

- (NSString *) _makeWebRequest: (NSString *) request
{
	NSLog(@"%@", request);
	NSURL *url = [NSURL URLWithString: [BASEURL stringByAppendingString: request]];
	NSString *result = [NSString stringWithContentsOfURL: url];
	return result;
}

- (void) applicationDidFinishLaunching:(NSNotification *)aNotification 
{
	NSLog(@"didFinishLaunching");
	
	[tableView setDoubleAction: @selector(addToiTunesPlaylist:)];
	
	// Create two dummy objects and add them to the list
	MBTune *tune1 = [[[MBTune alloc] init] autorelease];
	[tune1 setTrackID: @"F36B634931C2E9A0"];
	[tune1 setTitle: @"When Summer Comes"];
	[tune1 setArtist: @"Pepper"];
	[tune1 setLength: @"3:16"];
	[tune1 setRequester: @"John"];

	MBTune *tune2 = [[[MBTune alloc] init] autorelease];
	[tune2 setTrackID: @"57802A1965D11511"];
	[tune2 setTitle: @"Parachute"];
	[tune2 setArtist: @"Sean Lennon"];
	[tune2 setLength: @"3:19"];
	[tune2 setRequester: @"Paul"];	
	
	[self willChangeValueForKey: kRequests];
	[requests addObject: tune1];
	[requests addObject: tune2];
	[self didChangeValueForKey: kRequests];
	
	// Get playlists from iTunes
	// Update Popup - button
	// Select playlist that is saved to prefs.

}

	
	
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
	
	[iTunes_ addID: trackID toPlaylist: playlist];
}

- (void) checkRequests
{	
	// Add new requests to the array.
	
	NSLog(@"check requests");
	return;
	NSString *s = @"http://localhost:15800/new-requests/";
	NSString *result = [NSString stringWithContentsOfURL: [NSURL URLWithString: s]];
	NSLog(result);
	
	// parse the result and update the array
	
}

- (void) querySong
{
	NSString *ident = [self _runAppleScript: getTrackTemplate_];
	NSLog(@"Playing ID: %@", ident);
	
	// Make the http request
	NSString *str = [NSString stringWithFormat: @"http://localhost:15800/now-playing?songid=%@", ident];
	//NSString *result = [NSString stringWithContentsOfURL: [NSURL URLWithString: str]];
	//NSLog(result);
}

- (IBAction) getNextSongs: (id) sender
{
	NSLog(@"get next songs");	
	NSArray *songList = [iTunes_ nextFive];
	NSMutableString *queryString = [NSMutableString string];
	
	for (int i = 0;   i < [songList count] && i < 5; i++) {
		NSString *item = [NSString stringWithFormat: @"song%d=%@&", i+1, [songList objectAtIndex: i]];
		[queryString appendString: item];
	}
	
	NSLog(@"upcoming: %@", songList);	
	NSLog(@"queryString: %@", queryString);		
- (IBAction) startServer: (id) sender
{
	NSLog(@"Start Server");
	serverTask_ = [NSTask launchedTaskWithLaunchPath: PYTHON
		arguments: [NSArray arrayWithObject: [[NSBundle mainBundle] pathForResource:@"webserver" ofType:@"py"]]];
				
	[serverTask_ retain];
}

- (IBAction) stopServer: (id) sender
{
	NSLog(@"Stop Server");
	[serverTask_ terminate];
	[serverTask_ release];
}

- (id) init
{
	self = [super init];
	if (self != nil) {
		requests = [[NSMutableArray alloc] init];
		serverTask_ = nil;
		//requestCheckTimer_ = [NSTimer scheduledTimerWithTimeInterval: 21 target: self selector: @selector(checkRequests) userInfo: nil repeats: YES];
		//songQueryTimer_ = [NSTimer scheduledTimerWithTimeInterval: 13 target: self selector: @selector(querySong) userInfo: nil repeats: YES];
		
		iTunes_ = [[MBiTunes alloc] init];
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
	[serverTask_  terminate];
	[serverTask_ release];
	[super dealloc];
}


@end
