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

- (NSString *) _makeWebRequest: (NSString *) request
{
	NSLog(@"%@", request);
	NSURL *url = [NSURL URLWithString: [BASEURL stringByAppendingString: request]];
	NSString *result = [NSString stringWithContentsOfURL: url];
	return result;
}

- (NSString *) _iTunesLibraryFilePath
{
	NSUserDefaults *defaults = [[[NSUserDefaults alloc] init] autorelease];
	[defaults synchronize];
	[defaults addSuiteNamed: @"com.apple.iApps"];
	NSArray *iTunesDBURLs = [[defaults dictionaryRepresentation] objectForKey: @"iTunesRecentDatabases"];

	if (!iTunesDBURLs)
		return nil;
	
	NSString *libraryURL;
	NSEnumerator *e = [iTunesDBURLs objectEnumerator];
	while (libraryURL = [e nextObject])
	{
		NSString *libraryPath = [[NSURL URLWithString: libraryURL] path];
		if ([[NSFileManager defaultManager] fileExistsAtPath: libraryPath])
			return libraryPath;
	}
	
	return nil;
}

#pragma mark -

- (void) fetchRequests
{	
	NSLog(@"get requests");
	
	//	if (! serverTask_) return;
	NSString *result = [self _makeWebRequest: @"new-requests/"];
	
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
	NSString *request = [NSString stringWithFormat: @"now-playing?songid=%@", ident];
	[self _makeWebRequest: request];
}

- (void) reportNextSongs
{
	NSArray *songList = [iTunes_ nextFive];
	NSMutableString *queryString = [NSMutableString string];
	
	for (int i = 0;   i < [songList count] && i < 5; i++)
		[queryString appendString: [NSString stringWithFormat: @"song%d=%@&", i+1, [songList objectAtIndex: i]]];
	
	[self _makeWebRequest: [@"coming-up?" stringByAppendingString: queryString]];
}

- (void) reportNowPlaying
{
	[self reportCurrentSong];
	[self reportNextSongs];
}


#pragma mark -

#pragma mark IBActions

- (IBAction) addToiTunesPlaylist: (id) sender
{
	NSLog(@"addToiTunes");
	
	MBTune* track = nil;
	if ([sender isKindOfClass: [NSTableView class]]) {
		if ([tableView clickedRow] == -1) return;
		track = [[arrayController arrangedObjects] objectAtIndex: [tableView clickedRow]];
	} else {
		track = [[arrayController selectedObjects] objectAtIndex: 0];	
	}
	
	if (! track) return;
	
	NSString *playlist = @"radio";
	[iTunes_ addID: [track trackID] toPlaylist: playlist];
}

- (IBAction) getNextSongs: (id) sender
{
	NSLog(@"get next songs");	
	[self reportNextSongs];
}

- (IBAction) updateRequests: (id) sender
{
	NSLog(@"update Requests");
	[self fetchRequests];
}

- (IBAction) startServer: (id) sender
{
	NSLog(@"Start Server");
	
	NSString *libraryPath = [self _iTunesLibraryFilePath];
	NSString *port = [[NSUserDefaults standardUserDefaults] objectForKey: @"networkPort"];
					  
	NSLog(@"%@ %@", libraryPath, port);
	
	if (!libraryPath || !port)
		return;
	
	serverTask_ = [NSTask 
		launchedTaskWithLaunchPath: PYTHON
		arguments: [NSArray arrayWithObjects: 
			[[NSBundle mainBundle] pathForResource:@"webserver" ofType:@"py"],
			@"--port", port,
			@"--library", libraryPath,
			nil]];
				
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

- (void) applicationDidFinishLaunching:(NSNotification *)aNotification 
{
	NSLog(@"didFinishLaunching");
	
	[tableView setDoubleAction: @selector(addToiTunesPlaylist:)];
	
	// Get playlists from iTunes
	// Update Popup - button
	// Select playlist that is saved to prefs.
}


- (void)applicationWillTerminate:(NSNotification *)aNotification
{
	NSLog(@"willTerminate");
	[self stopServer:nil];
}

#pragma mark -

- (id) init
{
	self = [super init];
	if (self != nil) {
		requests = [[NSMutableArray alloc] init];
		serverTask_ = nil;
		requestCheckTimer_ = [NSTimer scheduledTimerWithTimeInterval: 21 target: self selector: @selector(fetchRequests) userInfo: nil repeats: YES];
		nowPlayingReportTimer_ = [NSTimer scheduledTimerWithTimeInterval: 13 target: self selector: @selector(reportNowPlaying) userInfo: nil repeats: YES];
		
		iTunes_ = [[MBiTunes alloc] init];
	}
	return self;
}

- (void) dealloc
{
	NSLog(@"dealloc");
	
	[requestCheckTimer_ invalidate];
	[requestCheckTimer_ release];
	[nowPlayingReportTimer_ invalidate];
	[nowPlayingReportTimer_ release];

	[requests release];
	[iTunes_ release];
	[super dealloc];
}

@end
