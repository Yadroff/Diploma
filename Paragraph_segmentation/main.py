import Letter
import cv2
import numpy as np
from matplotlib import pyplot as plt
from timeit import default_timer as timer
import os


# function finds the corners given the top,bottom,left,and right maximum pixels
def findCorners(bound):
    c1 = [bound[3][0], bound[0][1]]
    c2 = [bound[1][0], bound[0][1]]
    c3 = [bound[1][0], bound[2][1]]
    c4 = [bound[3][0], bound[2][1]]
    return [c1, c2, c3, c4]


# function finds the minimization of the weighted within-class variance
# Adapted from: https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html
def findThresh(data):
    Binsize = 50
    # find density and bounds of histogram of data
    density, bds = np.histogram(data, bins=Binsize)
    # normalize the histogram values
    norm_dens = (density) / float(sum(density))
    # find discrete cumulative density function
    cum_dist = norm_dens.cumsum()
    # initial values to be overwritten
    fn_min = np.inf
    thresh = -1
    bounds = range(1, Binsize)
    # begin minimization routine
    for itr in range(0, Binsize):
        if (itr == Binsize - 1):
            break;
        p1 = np.asarray(norm_dens[0:itr])
        p2 = np.asarray(norm_dens[itr + 1:])
        q1 = cum_dist[itr]
        q2 = cum_dist[-1] - q1
        b1 = np.asarray(bounds[0:itr])
        b2 = np.asarray(bounds[itr:])
        # find means
        m1 = np.sum(p1 * b1) / q1
        m2 = np.sum(p2 * b2) / q2
        # find variance
        v1 = np.sum(((b1 - m1) ** 2) * p1) / q1
        v2 = np.sum(((b2 - m2) ** 2) * p2) / q2

        # calculate minimization function and replace values
        # if appropriate
        fn = v1 * q1 + v2 * q2
        if fn < fn_min:
            fn_min = fn
            thresh = itr
    return thresh, bds[thresh]


def dist(P1, P2):
    return np.sqrt((P1[0] - P2[0]) ** 2 + (P1[1] - P2[1]) ** 2)


# function takes two rectangles of corners and combines them into a single rectangle
def mergeBoxes(c1, c2):
    newRect = []
    # find new corner for the top left
    cx = min(c1[0][0], c2[0][0])
    cy = min(c1[0][1], c2[0][1])
    newRect.append([cx, cy])
    # find new corner for the top right
    cx = max(c1[1][0], c2[1][0])
    cy = min(c1[1][1], c2[1][1])
    newRect.append([cx, cy])
    # find new corner for bottm right
    cx = max(c1[2][0], c2[2][0])
    cy = max(c1[2][1], c2[2][1])
    newRect.append([cx, cy])
    # find new corner for bottm left
    cx = min(c1[3][0], c2[3][0])
    cy = max(c1[3][1], c2[3][1])
    newRect.append([cx, cy])
    return newRect


# given a list of corners that represent the corners of a box, find the center of that box
def findCenterCoor(c1):
    width = abs(c1[0][0] - c1[1][0])
    height = abs(c1[0][1] - c1[3][1])
    return ([c1[0][0] + (width / 2.0), c1[0][1] + (height / 2.0)])


# take two points and find their slope
def findSlope(p1, p2):
    if (p1[0] - p2[0] == 0):
        return np.inf
    return (p1[1] - p2[1]) / (p1[0] - p2[0])


# takes point and set of corners and checks if the point is within the bounds
def isInside(p1, c1):
    if (p1[0] >= c1[0][0] and p1[0] <= c1[1][0] and p1[1] >= c1[0][1] and p1[1] <= c1[2][1]):
        return True
    else:
        return False


def findArea(c1):
    return abs(c1[0][0] - c1[1][0]) * abs(c1[0][1] - c1[3][1])


def get_corners_of_bboxes(thresholded_img):
    bndingBx = []  # holds bounding box of each countour
    corners = []
    contours, heirarchy = cv2.findContours(thresholded_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    # find the rectangle around each contour
    for num in range(0, len(contours)):
        # make sure contour is for letter and not cavity
        if (heirarchy[0][num][3] == -1):
            left = tuple(contours[num][contours[num][:, :, 0].argmin()][0])
            right = tuple(contours[num][contours[num][:, :, 0].argmax()][0])
            top = tuple(contours[num][contours[num][:, :, 1].argmin()][0])
            bottom = tuple(contours[num][contours[num][:, :, 1].argmax()][0])
            bndingBx.append([top, right, bottom, left])
    # find the edges of each bounding box
    for bx in bndingBx:
        corners.append(findCorners(bx))
    return corners


def remove_outliers(img, th_img, corners):
    err = 2  # error value for minor/major axis ratio
    Area = []  # holds the areas of each bounding boxes
    # go through each corner and append its area to the list
    for corner in corners:
        Area.append(findArea(corner))
    Area = np.asarray(Area)
    avgArea = np.mean(Area)
    stdArea = np.std(Area)
    outlier = (Area < avgArea - stdArea)  # find the out liers, these are probably the dots
    for num in range(0, len(outlier)):
        dot = False
        if (outlier[num]):  # if the outlier is a dot, perform operations
            # create new image of black pixels
            black = np.zeros((len(img), len(img[0])), np.uint8)
            # add white pixels in the region that contains the outlier
            cv2.rectangle(black, (corners[num][0][0], corners[num][0][1]), (corners[num][2][0], corners[num][2][1]),
                          (255, 255), -1)
            # perform bitwise operation on original image to isolate outlier
            fin = cv2.bitwise_and(th_img, black)
            # find the contours of this outlier
            tempCnt, tempH = cv2.findContours(fin, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            # loop, due to structure of countours
            for cnt in tempCnt:
                # create bounding rectangle of contour
                rect = cv2.minAreaRect(cnt)
                # calculate major and minor axis
                axis1 = rect[1][0] / 2.0
                axis2 = rect[1][1] / 2.0
                if (axis1 != 0 and axis2 != 0):  # do not perform if image has 0 dimension
                    ratio = axis1 / axis2  # calculate ratio of axis
                    # if ratio is close to 1 (circular), then most likely a dot
                    if ratio > 1.0 - err and ratio < err + 1.0:
                        dot = True
            # if contour is a dot, we want to connect it to the closest
            # bounding box that is beneath it
            if dot:
                bestCorner = corners[num]
                closest = np.inf
                for crn in corners:  # go through each set of corners
                    # find width and height of bounding box
                    width = abs(crn[0][0] - crn[1][0])
                    height = abs(crn[0][1] - crn[3][1])
                    # check to make sure character is below in position (greater y value)
                    if (corners[num][0][1] > crn[0][1]):
                        continue  # if it's above the dot we don't care
                    elif dist(corners[num][0], crn[0]) < closest and crn != corners[
                        num]:  # and (findSlope(findCenterCoor(corners[num]),crn[0])) > 0:
                        # if(findArea(mergeBoxes(corners[num],crn))> avgArea+stdArea):
                        #     continue
                        # check the distance if it is below the dot
                        cent = findCenterCoor(crn)
                        bestCorner = crn
                        closest = dist(corners[num][0], crn[0])
                # modify the coordinates of the pic to include the dot
                # print(bestCorner)
                newCorners = mergeBoxes(corners[num], bestCorner)
                corners.append(newCorners)
                # print(newCorners)
                corners[num][0][0] = 0
                corners[num][0][1] = 0
                corners[num][1][0] = 0
                corners[num][1][1] = 0
                corners[num][2][0] = 0
                corners[num][2][1] = 0
                corners[num][3][0] = 0
                corners[num][3][1] = 0
                bestCorner[0][0] = 0
                bestCorner[0][1] = 0
                bestCorner[1][0] = 0
                bestCorner[1][1] = 0
                bestCorner[2][0] = 0
                bestCorner[2][1] = 0
                bestCorner[3][0] = 0
                bestCorner[3][1] = 0


def get_list_of_word_coordinates(corners):
    AllLetters = []  # Turn letters into objects
    counter = 0
    for bx in corners:
        width = abs(bx[1][0] - bx[0][0])
        height = abs(bx[3][1] - bx[0][1])
        if width * height == 0:
            continue
        plt.plot([bx[0][0], bx[1][0]], [bx[0][1], bx[1][1]], 'g-', linewidth=2)
        plt.plot([bx[1][0], bx[2][0]], [bx[1][1], bx[2][1]], 'g-', linewidth=2)
        plt.plot([bx[2][0], bx[3][0]], [bx[2][1], bx[3][1]], 'g-', linewidth=2)
        plt.plot([bx[3][0], bx[0][0]], [bx[3][1], bx[0][1]], 'g-', linewidth=2)
        newLetter = Letter.Letter([bx[0][0], bx[0][1]], [height, width], counter)
        AllLetters.append(newLetter)
        counter += 1
    AllLetters.sort(key=lambda letter: letter.getY() + letter.getHeight())
    return AllLetters


def get_y_coordinate_distances(AllLetters):
    # project the y coordinates of the letters on to the y axis
    prjYCoords = []
    letter_start_y_coords = []
    for letter in AllLetters:
        prjYCoords.append(letter.getY() + letter.getHeight())
        letter_start_y_coords.append(letter.getY())
        plt.plot([letter.getX(), letter.getX() + letter.getWidth()], [letter.getY(), letter.getY()], 'b-', linewidth=2)
        plt.plot([letter.getX() + letter.getWidth(), letter.getX() + letter.getWidth()],
                 [letter.getY(), letter.getY() + letter.getHeight()], 'b-', linewidth=2)
        plt.plot([letter.getX() + letter.getWidth(), letter.getX()],
                 [letter.getY() + letter.getHeight(), letter.getY() + letter.getHeight()], 'b-', linewidth=2)
        plt.plot([letter.getX(), letter.getX()], [letter.getY() + letter.getHeight(), letter.getY()], 'b-', linewidth=2)
    '''for c in prjYCoords:
        plt.plot(0, c,'ro')
    plt.show()'''

    # find distances between coordinates
    coorDists = [0]
    for num in range(1, len(prjYCoords)):
        valCur = prjYCoords[num]
        valPast = prjYCoords[num - 1]
        coorDists.append(valCur - valPast)
    return prjYCoords, coorDists, letter_start_y_coords


def reject_outliers(data, m=1):
    return data[abs(data - np.mean(data)) < m * np.std(data)]


def get_mean_distance_between_lines(coorDists):
    valid_coorDists = [i for i in coorDists if i > 5]
    valid_coorDists = reject_outliers(np.asarray(valid_coorDists)).tolist()
    meanCoord = float(sum(valid_coorDists)) / float(len(valid_coorDists))
    stdCoord = np.std(valid_coorDists)
    return meanCoord, stdCoord


def get_y_coordinate_indices(coorDists):
    start = 0
    end = 0
    # meanCoord = float(sum(coorDists))/float(len(coorDists))
    # stdCoord = np.std(coorDists)
    meanCoord, stdCoord = get_mean_distance_between_lines(coorDists)
    print(meanCoord, stdCoord)

    medPoints = []
    for num in range(0, len(coorDists)):
        if coorDists[num] > meanCoord - 2.0 * stdCoord:
            end = num
            medPoints.append(int(start + (end - start) / 2.0))
            start = num
    medPoints.append(int(start + (len(coorDists) - 1 - start) / 2.0))
    return medPoints


def get_ymin(letter_start_y_coords, medPoints, previous_para_start, previous_para_ymax):
    ymin = letter_start_y_coords[medPoints[previous_para_start]]
    if (ymin < previous_para_ymax):
        start_idx = medPoints[previous_para_start] + 1
        if previous_para_start < len(medPoints) - 1:
            end_idx = medPoints[previous_para_start + 1]
        else:
            end_idx = len(letter_start_y_coords)
        while (start_idx < end_idx and ymin <= previous_para_ymax):
            ymin = letter_start_y_coords[start_idx]
            start_idx += 1
        if (ymin < previous_para_ymax):
            ymin = previous_para_ymax + meanCoord + stdCoord
    return ymin


def process_image(img, file_name, logs_dir='./logs/'):
    logs_dir = os.path.join(logs_dir, os.path.splitext(file_name)[0])
    os.makedirs(os.path.join(logs_dir), exist_ok=True)
    blur = cv2.GaussianBlur(img, (15, 15), 5)
    cv2.imwrite(os.path.join(logs_dir, 'blur.png'), blur)
    # th3 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # th3 = cv2.bitwise_not(th3)
    ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cv2.imwrite(os.path.join(logs_dir, 'thresh.png'), th3)

    corners = get_corners_of_bboxes(th3)
    remove_outliers(img, th3, corners)
    AllLetters = get_list_of_word_coordinates(corners)
    # plt.imshow(th3,'gray')
    # plt.show()
    # plt.clf()

    prjYCoords, coorDists, letter_start_y_coords = get_y_coordinate_distances(AllLetters)
    medPoints = get_y_coordinate_indices(coorDists)

    lines = []
    for num in range(0, len(medPoints)):
        lines.append(prjYCoords[medPoints[num]])
        # plt.plot([0,5000],[prjYCoords[medPoints[num]],prjYCoords[medPoints[num]]],'r-')
        # cv2.line(out,(0,prjYCoords[medPoints[num]]),(out.shape[1], prjYCoords[medPoints[num]]), (0,0,255), 2)
        # cv2.line(out,(0,letter_start_y_coords[medPoints[num]]),(out.shape[1], letter_start_y_coords[medPoints[num]]), (255,0,0), 2)

    print('letter_start_y_coords: {}'.format(letter_start_y_coords))
    print('letter_endin_y_coords: {}'.format(prjYCoords))
    print('coorDists: {}'.format(coorDists))
    print('medPoints: {}'.format(medPoints))
    print('lines: {}'.format(lines))

    line_distances = [0]
    for num in range(1, len(lines)):
        valCur = lines[num]
        valPast = lines[num - 1]
        line_distances.append(valCur - valPast)
    print('line_distances: {}'.format(line_distances))

    previous_para_start = 0
    previous_para_end = 0
    previous_para_ymax = 0
    meanCoord, stdCoord = get_mean_distance_between_lines(line_distances)
    print(meanCoord, stdCoord)
    if stdCoord < 10:
        stdCoord = 10
    bboxes = []
    for num in range(1, len(line_distances)):
        if line_distances[num] > meanCoord + 1.0 * stdCoord:
            previous_para_end = num - 1
            ymin = get_ymin(letter_start_y_coords, medPoints, previous_para_start, previous_para_ymax)
            bboxes.append({
                "xmin": 10,
                "ymin": ymin - 5,
                "xmax": img.shape[1] - 10,
                "ymax": lines[previous_para_end] + 5
            })
            previous_para_start = num
            previous_para_ymax = lines[previous_para_end]

    ymin = get_ymin(letter_start_y_coords, medPoints, previous_para_start, previous_para_ymax)
    bboxes.append({
        "xmin": 10,
        "ymin": ymin - 5,
        "xmax": img.shape[1] - 10,
        "ymax": lines[-1] + 5
    })
    return bboxes


def process_file(image_path, output_dir):
    img = cv2.imread(image_path, 0)
    bboxes = process_image(img, os.path.basename(image_path))
    out = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    for bbox in bboxes:
        cv2.rectangle(out, (bbox["xmin"], bbox["ymin"]), (bbox["xmax"], bbox["ymax"]), (255, 0, 0), 5)
    out_filename = os.path.splitext(os.path.basename(image_path))[0] + '.png'
    # cv2.imwrite(os.path.join(output_dir, "th_" + out_filename), th3)
    cv2.imwrite(os.path.join(output_dir, out_filename), out)


def process_dir(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.png'):
            process_file(os.path.join(input_dir, filename), output_dir)


if __name__ == "__main__":
    st = timer()
    process_dir('./images/', './outputs/')
    # process_file('./images/1.png',  './outputs/')
    end = timer()
    print("Processing completed in {:0.2f}s".format(end - st))
