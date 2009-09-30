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

-(NSString*) path
{
	return path_;
}

-(NSString*) title
{
	return title_;
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
	return length_;
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

-(void) setPath: (NSString*) path
{
	if (path == path_)
		return;
	
	[path_ release];
	path_ = [path retain];
}

-(void) setTitle: (NSString*) title
{
	if (title == title_)
		return;
	
	[title_ release];
	title_ = [title retain];
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

-(void) setLength: (NSString*) length
{
	if (length == length_)
		return;
	
	[length_ release];
	length_ = [length retain];
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
			@"[%@] %@ - %@", trackID_, artist_, title_];
}

@end
