//
//  MBTune.m
//  MBR
//
//  Created by Jonathan on 9/23/09.
//

#import "MBTune.h"

@implementation MBTune

- (int) ID
{
	return requestID_;
}

- (NSString*) artist
{
	return artist_;
}

- (NSString*) title
{
	return title_;
}

- (NSString*) album
{
	return album_;
}

- (NSString*) genre
{
	return genre_;
}

- (NSString*) requester
{
	return requester_;
}

- (NSString*) dedication
{
	return dedication_;
}

- (NSString*) trackID
{
	return trackID_;
}

- (NSString*) duration
{
	return duration_;
}

- (NSDate*) requestTime
{
	return requestTime_;
}

#pragma mark -

- (void) setArtist: (NSString*) artist
{
	if (artist == artist_)
		return;
	
	[artist_ release];
	artist_ = [artist retain];
}

- (void) setTitle: (NSString*) title
{
	if (title == title_)
		return;
	
	[title_ release];
	title_ = [title retain];
}

- (void) setAlbum: (NSString*) album
{
	if (album == album_)
		return;
	
	[album_ release];
	album_ = [album retain];
}

- (void) setGenre: (NSString*) genre
{
	if (genre == genre_)
		return;
	
	[genre_ release];
	genre_ = [genre retain];
}

- (void) setRequester: (NSString*) requester
{
	if (requester == requester_)
		return;
	
	[requester_ release];
	requester_ = [requester retain];
}

- (void) setDedication: (NSString*) dedication
{
	if (dedication == dedication_)
		return;
	
	[dedication_ release];
	dedication_ = [dedication retain];
}

- (void) setTrackID: (NSString*) trackID
{
	if (trackID == trackID_)
		return;
	
	[trackID_ release];
	trackID_ = [trackID retain];
}

- (void) setDuration: (NSString*) length
{
	if (length == duration_)
		return;
	
	[duration_ release];
	duration_ = [length retain];
}

- (void) setRequestTime: (NSDate*) requestTime
{
	if (requestTime == requestTime_)
		return;
	
	[requestTime_ release];
	requestTime_ = [requestTime retain];
}

- (void) setRequestID: (int) ID
{
	requestID_ = ID;
}

#pragma mark -

- (id) initWithXML: (NSXMLElement *) element
{
	self = [self init];
	
	if (!self) return nil;
	
	NSXMLElement *detail;
	NSArray *details = [element children];
	NSEnumerator *detailEnum = [details objectEnumerator];
	while (detail = [detailEnum nextObject]) {
		NSString *tag = [detail name];
		NSString *content = [detail stringValue];
		
		if ([tag isEqualToString: @"time"]) {
			NSDate *time = [NSDate dateWithTimeIntervalSince1970: [content doubleValue]];
			[self setRequestTime: time];
		}
		else if ([tag isEqualToString: @"requestedby"])
			[self setRequester: content];
		else if ([tag isEqualToString: @"dedication"])
			[self setDedication: content];
		else if ([tag isEqualToString: @"song"]) {				
			[self setTrackID: [[detail attributeForName:@"id"] stringValue]];
			
			NSXMLElement *info;
			NSArray *songInfo = [detail children];
			NSEnumerator *songInfoEnum = [songInfo objectEnumerator];
			while (info = [songInfoEnum nextObject]) {
				NSString *s = [info name];
				NSString *property = [info stringValue];
				
				if ([s isEqualToString: @"artist"])
					[self setArtist: property];
				else if ([s isEqualToString: @"title"])
					[self setTitle: property];
				else if ([s isEqualToString: @"album"])
					[self setAlbum: property];
				else if ([s isEqualToString: @"genre"])
					[self setGenre: property];
				else if ([s isEqualToString: @"duration"]) {
					int duration = [property intValue];
					int seconds = duration / 1000;
					int minutes = seconds / 60;
					seconds -= minutes*60;
					[self setDuration: [NSString stringWithFormat: @"%d:%d", minutes, seconds]];
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

- (NSString*) description
{
	return [NSString stringWithFormat:
			@"[%@] %@ %@ - %@\nded: %@, %req: %@\ndur: %@ time: %@", trackID_, genre_, artist_, title_, dedication_, requester_, duration_, requestTime_];
}

@end

