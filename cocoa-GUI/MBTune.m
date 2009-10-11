//
//  MBTune.m
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import "MBTune.h"


@implementation MBTune

-(NSString*) artist
{
	return artist_;
}

-(NSString*) title
{
	return title_;
}

-(NSString*) album
{
	return album_;
}

-(NSString*) genre
{
	return genre_;
}

-(NSString*) requester
{
	return requester_;
}

-(NSString*) dedication
{
	return dedication_;
}

-(NSString*) trackID
{
	return trackID_;
}

-(NSString*) length
{
	return duration_;
}

-(NSDate*) requestTime
{
	return requestTime_;
}

-(void) setArtist: (NSString*) artist
{
	if (artist == artist_)
		return;
	
	[artist_ release];
	artist_ = [artist retain];
}

-(void) setTitle: (NSString*) title
{
	if (title == title_)
		return;
	
	[title_ release];
	title_ = [title retain];
}

-(void) setAlbum: (NSString*) album
{
	if (album == album_)
		return;
	
	[album_ release];
	album_ = [album retain];
}

-(void) setGenre: (NSString*) genre
{
	if (genre == genre_)
		return;
	
	[genre_ release];
	genre_ = [genre retain];
}

-(void) setRequester: (NSString*) requester
{
	if (requester == requester_)
		return;
	
	[requester_ release];
	requester_ = [requester retain];
}

-(void) setDedication: (NSString*) dedication
{
	if (dedication == dedication_)
		return;
	
	[dedication_ release];
	dedication_ = [dedication retain];
}

-(void) setTrackID: (NSString*) trackID
{
	if (trackID == trackID_)
		return;
	
	[trackID_ release];
	trackID_ = [trackID retain];
}

-(void) setDuration: (NSString*) length
{
	if (length == duration_)
		return;
	
	[duration_ release];
	duration_ = [length retain];
}

-(void) setRequestTime: (NSDate*) requestTime
{
	if (requestTime == requestTime_)
		return;
	
	[requestTime_ release];
	requestTime_ = [requestTime retain];
}

-(NSString*) description
{
	return [NSString stringWithFormat:
			@"[%@] %@ %@ - %@\nded: %@, %req: %@\ndur: %@ time: %@", trackID_, genre_, artist_, title_, dedication_, requester_, duration_, requestTime_];
}

- (id) initWithXML: (NSXMLElement *)element
{
	self = [self init];
	NSArray *details = [element children];
	NSEnumerator *detailEnumerator = [details objectEnumerator];
	NSXMLElement *detail;
	while (detail = [detailEnumerator nextObject]) {
		NSString* name = [detail name];
		
		if ([name isEqualToString: @"time"]) {
			NSDate *time = [NSDate dateWithTimeIntervalSince1970: [[detail stringValue] doubleValue]];
			[self setRequestTime: time];
		}
		else if ([name isEqualToString: @"requestedby"])
			[self setRequester: [detail stringValue]];
		else if ([name isEqualToString: @"dedication"])
			[self setDedication: [detail stringValue]];
		else if ([name isEqualToString: @"song"]) {				
			[self setTrackID: [[detail attributeForName:@"id"] stringValue]];
			
			NSArray *songInfo = [detail children];
			NSEnumerator *songInfoEnumerator = [songInfo objectEnumerator];
			NSXMLElement *info;
			while (info = [songInfoEnumerator nextObject]) {
				NSString *s = [info name];
				
				if ([s isEqualToString: @"artist"])
					[self setArtist: [info stringValue]];
				else if ([s isEqualToString: @"title"])
					[self setTitle: [info stringValue]];
				else if ([s isEqualToString: @"album"])
					[self setAlbum: [info stringValue]];
				else if ([s isEqualToString: @"genre"])
					[self setGenre: [info stringValue]];
				else if ([s isEqualToString: @"duration"]) {
				}
			}
		}
	}
	return self;
}

- (id) init
{
	self = [super init];
	if (self != nil) {
		//
	}
	return self;
}

- (void) dealloc
{
	//
	[super dealloc];
}


@end
