import enum
import math
import sys
from itertools import groupby
import geopy.distance

from django.http.request import split_domain_port

def correct_longitude(lon):
    return lon - 360

def distance(p1, p2):
    point1 = (p1[1], p1[0])
    point2 = (p2[1], p2[0])
    return geopy.distance.geodesic(point1, point2).km

def midpoint(x1, y1, x2, y2):
#Input values as degrees

#Convert to radians
    lat1 = math.radians(x1)
    lon1 = math.radians(y1)
    lat2 = math.radians(x2)
    lon2 = math.radians(y2)

    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)
    lat3 = math.atan2(math.sin(lat1) + math.sin(lat2), \
           math.sqrt((math.cos(lat1) + bx) * (math.cos(lat1) \
           + bx) + by**2))
    lon3 = lon1 + math.atan2(by, math.cos(lat1) + bx)

    return [round(math.degrees(lat3), 2), round(math.degrees(lon3), 2)]


def connect_points(p1, p2):
    #print('Connection points')
    distance_ = distance(p1, p2)
    max_level = int(math.log(distance_ / 50, 2))
    points = [p1, p2]
    while max_level > 0:
        new_points = []
        for i in range(1, len(points)):
            p_1 = points[i - 1]
            p_2 = points[i]
            new_points.append(p_1)
            #print('Looking for midpoint in: ')
            #print(p_1)
            #print(p_2)
            new_points.append(midpoint_by_given_format_points(p_1, p_2))
        new_points.append(points[-1])
        points = new_points
        max_level -=1
    return points

def midpoint_by_given_format_points(p1, p2):
    mp = midpoint(p1[1], p1[0], p2[1], p2[0])
    midpoint_ = [mp[1], mp[0]]
    return midpoint_

class CurveAddStatus(enum.Enum):
    begining_and_reverse = 4
    begining = 3
    end_and_reverse = 2
    end = 1

    def merge_coords(status, coord1, coord2):
        if status == 1:
            connected_points = connect_points(coord2[-1], coord1[0])
            return coord2 + connected_points + coord1
        if status == 2:
            reversed = list(reversed(coord1))
            connected_points = connect_points(coord2[-1], reversed[0])
            return coord2 + connected_points + reversed
        if status == 3:
            connected_points = connect_points(coord1[-1], coord2[0])
            return coord1 + connected_points + coord2
        if status == 4:
            reversed = list(reversed(coord2))
            connected_points = connect_points(coord1[-1], reversed[0])
            return coord1 + connected_points + reversed

class ClosestAddInfoExpanded:
    index = None
    closest_add_info = None

    def __init__(self, index, closest_add_info):
        self.index = index
        self.closest_add_info = closest_add_info
        

class ClosestAddInfo:
    distance = None
    feature = None
    curve_add_status = CurveAddStatus.end.value

    def __init__(self, distance, feature, curve_add_status):
        self.distance = distance
        self.feature = feature
        self.curve_add_status = curve_add_status

class AnomalyCurve:
    needs_reverse = False
    feature = None
    coordinates = []
    start_point = []
    end_point = []

    def __init__(self, feature):
        self.feature = feature
        self.coordinates = feature['geometry']['coordinates']
        self.start_point = self.coordinates[0]
        self.end_point = self.coordinates[-1]

    def is_closed(self):
        return self.start_point == self.end_point

    def init_distance(self):
        return distance(self.start_point, self.end_point)

    def closest_distance(self, curve):
        class ComparanceInfo:
            distance = 0
            curve_add_status = CurveAddStatus.end.value
            def __init__(self, distance, curve_add_status):
                self.distance = distance
                self.curve_add_status = curve_add_status

        def comparance_distance(comparance_info):
            return comparance_info.distance
            
        comparance = [
            ComparanceInfo(distance(self.start_point, curve.start_point), CurveAddStatus.begining_and_reverse.value), 
            ComparanceInfo(distance(self.start_point, curve.end_point), CurveAddStatus.begining.value),  
            ComparanceInfo(distance(self.end_point, curve.start_point), CurveAddStatus.end.value),  
            ComparanceInfo(distance(self.end_point, curve.end_point), CurveAddStatus.end_and_reverse.value)]
        #for comp in comparance:
        #    print(comp.curve_add_status)
        #    print(comp.distance)
        info = min(comparance, key=comparance_distance)
        return ClosestAddInfo(info.distance, self.feature, info.curve_add_status)

    def merged_feature(self, feature_info):
        self_coords = self.feature['geometry']['coordinates']
        feature_coords = feature_info.closest_add_info.feature['geometry']['coordinates']
        status = feature_info.closest_add_info.curve_add_status
        self.feature['geometry']['coordinates'] = CurveAddStatus.merge_coords(status, self_coords ,feature_coords)
        return self.feature

def last_coord(coords):
    return [coords[0], coords[1] - 0.00001]

def first_and_last_points(feature):
    first = feature['geometry']['coordinates'][0]
    last = feature['geometry']['coordinates'][-1]
    return [first, last]

def connect_feature_group(group):
    if False:
        north = []
        south = []
        for feat in group:
            if feat['geometry']['coordinates'][0][1] > 0:
                north.append(feat)
            else:
                south.append(feat)
        south_feat = south[0]
        del south[0]
        for feat in south:
            south_feat['geometry']['coordinates'] = south_feat['geometry']['coordinates'] + feat['geometry']['coordinates']
        north_feat = north[0]
        del north[0]
        for feat in north:
            north_feat['geometry']['coordinates'] = north_feat['geometry']['coordinates'] + feat['geometry']['coordinates']
        return [south_feat, north_feat]
    if len(group) == 1:
        feature = group[0]
        print(len(feature['geometry']['coordinates']))
        feature['geometry']['coordinates'].append(last_coord(feature['geometry']['coordinates'][0]))
        return [feature]
    connected_features = []
    copy = group
    i = 0
    while i < len(copy):
        #print('--------------')
        #print('New iteration')
        #print(i)
        #print(len(copy))
        #print('--------------')
        current_curve = AnomalyCurve(copy[i])
        if current_curve.is_closed():
            print('curve is closed')
            i += 1
            connected_features.append(current_curve.feature)
            continue
        nearest_curve = None

        #print('range')
        #print(range(i + 1, len(copy)))
        for y in range(i + 1, len(copy)):
            #print('iter y')
            #print(y)
            #print()
            additional_curve = AnomalyCurve(copy[y])
            if additional_curve.is_closed():
                continue
            info = additional_curve.closest_distance(current_curve)

            #print('init distance')
            #print(current_curve.init_distance())
            #print('info distance')
            #print(info.distance)
            if current_curve.init_distance() > info.distance or (info.distance - current_curve.init_distance()) < 100: 
                if nearest_curve == None:
                    #print('some2')
                    #print(info.distance)
                    nearest_curve = ClosestAddInfoExpanded(y,info)
                else:
                    #print(nearest_curve)
                    #print('some1')
                    #print(nearest_curve.closest_add_info.distance)
                    if nearest_curve.closest_add_info.distance > info.distance:
                        nearest_curve = ClosestAddInfoExpanded(y,info)
                    
        
        if nearest_curve == None:
            print('close curve')
            feature = current_curve.feature
            coords = feature['geometry']['coordinates']
            print(connect_points(coords[-1],coords[0]))
            feature['geometry']['coordinates'] = coords + connect_points(coords[-1],coords[0])
            #feature['geometry']['coordinates'].append(last_coord(feature['geometry']['coordinates'][0]))
            connected_features.append(feature)
            i += 1
            continue
        else:
            copy[i] = current_curve.merged_feature(nearest_curve)
            del copy[nearest_curve.index]
            continue
    return connected_features

def connect_features(features):
    def grouper(feature):
        return feature['properties']['title']

    connected_features = []
    #print('Unconnected features count: ')
    #print(len(features))
    for key, items in groupby(features, key=grouper):
        #print('key:')
        #print(key)
        connected_features += connect_feature_group(list(items))
    #print('Connected features count: ')
    #print(len(connected_features))
    return connected_features