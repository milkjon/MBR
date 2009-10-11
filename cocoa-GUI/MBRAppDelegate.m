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

- (void) fetchRequests
{	
	// Add new requests to the array.
	NSLog(@"get requests");
	
	//	if (! serverTask_) return;
	NSString *s = @"http://localhost:15800/new-requests/";
	NSString *result = [NSString stringWithContentsOfURL: [NSURL URLWithString: s]];
	
	// parse the result and update the array
	NSXMLDocument *d = [[NSXMLDocument alloc] initWithXMLString:result options:0 error:nil];
	NSArray *array = [d nodesForXPath:@"requestlist/request" error:nil];
	
	if ([array count] == 0) return;
	
	NSEnumerator *itemEnumerator = [array objectEnumerator];
	NSXMLElement *item;
	while (item = [itemEnumerator nextObject]) {
		MBTune *tune = [[MBTune alloc] initWithXML: item];
		 [self willChangeValueForKey: kRequests];
		 [requests addObject: tune];
		 [self didChangeValueForKey: kRequests];
	}
}

- (void) reportCurrentSong
{
	if (! serverTask_) return;
	
	NSString *ident = [iTunes_ currentlyPlaying];
	NSLog(@"Playing ID: %@", ident);
	
	// Make the http request
	NSString *str = [NSString stringWithFormat: @"now-playing?songid=%@", ident];
	//NSString *result = [NSString stringWithContentsOfURL: [NSURL URLWithString: str]];
	//NSLog(result);
}

#pragma mark IBActions

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

- (IBAction) getNextSongs: (id) sender
{
	NSLog(@"get next songs");	
	NSArray *songList = [iTunes_ nextFive];
	NSMutableString *queryString = [NSMutableString string];
	
	for (int i = 0;   i < [songList count] && i < 5; i++) {
		NSString *item = [NSString stringWithFormat: @"song%d=%@&", i+1, [songList objectAtIndex: i]];
		[queryString appendString: item];
	}
	
	[self _makeWebRequest: [@"coming-up?" stringByAppendingString: queryString]];
}

- (IBAction) updateRequests: (id) sender
{
	NSLog(@"update Requests");
	[self fetchRequests];
}

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
	serverTask_ = nil;
}

#pragma mark Notfications

- (void)applicationWillTerminate:(NSNotification *)aNotification
{
	NSLog(@"willTerminate");
	[self stopServer:nil];
}

- (void) applicationDidFinishLaunching:(NSNotification *)aNotification 
{
	NSLog(@"didFinishLaunching");
	
	[tableView setDoubleAction: @selector(addToiTunesPlaylist:)];

	// Get playlists from iTunes
	// Update Popup - button
	// Select playlist that is saved to prefs.
}

- (id) init
{
	self = [super init];
	if (self != nil) {
		requests = [[NSMutableArray alloc] init];
		serverTask_ = nil;
		//requestCheckTimer_ = [NSTimer scheduledTimerWithTimeInterval: 21 target: self selector: @selector(fetchRequests) userInfo: nil repeats: YES];
		//songQueryTimer_ = [NSTimer scheduledTimerWithTimeInterval: 13 target: self selector: @selector(reportCurrentSong) userInfo: nil repeats: YES];
		
		iTunes_ = [[MBiTunes alloc] init];
	}
	return self;
}

- (void) dealloc
{
	NSLog(@"dealloc");
	
	[requestCheckTimer_ invalidate];
	[requestCheckTimer_ release];
	[songQueryTimer_ invalidate];
	[songQueryTimer_ release];

	[requests release];
	[iTunes_ release];
	[super dealloc];
}


@end
