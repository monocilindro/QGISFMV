# -*- coding: utf-8 -*-
from QGIS_FMV.utils.QgsFmvUtils import (GetSensor,
                                        GetLine3DIntersectionWithPlane,
                                        GetFrameCenter,
                                        hasElevationModel)

from qgis.PyQt.QtCore import QSize, QPointF
from QGIS_FMV.video.QgsVideoUtils import VideoUtils as vut
from qgis.PyQt.QtCore import Qt, QPoint
from QGIS_FMV.geo import sphere as sphere
from qgis.PyQt.QtGui import (QPainter,
                         QPainterPath,
                         QColor,
                         QFont,
                         QPixmap,
                         QRadialGradient,
                         QPen,
                         QBrush,
                         QPolygonF)
try:
    from pydevd import *
except ImportError:
    None

RulerTotalMeasure = 0.0


class DrawToolBar(object):
    
    MAX_MAGNIFIER = 250

    @staticmethod
    def drawOnVideo(drawPtPos, drawLines, drawPolygon, drawRuler, drawCesure, painter, surface, gt):
        # Draw clicked points on video
        i = 1
        for pt in drawPtPos:
            DrawToolBar.drawPointOnVideo(i, pt, painter, surface, gt)
            i += 1

        # Draw clicked lines on video
        if len(drawLines) > 1:
            for idx, pt in enumerate(drawLines):
                if pt[0] is None:
                    continue
                else:
                    DrawToolBar.drawLinesOnVideo(
                        pt, idx, painter, surface, gt, drawLines)

        # Draw clicked Polygons on video
        if len(drawPolygon) > 1:
            poly = []
            if any(None == x[1] for x in drawPolygon):
                for pt in drawPolygon:
                    if pt[0] is None:
                        DrawToolBar.drawPolygonOnVideo(
                            poly, painter, surface, gt)
                        poly = []
                        continue
                    poly.append(pt)
                last_occurence = len(
                    drawPolygon) - drawPolygon[::-1].index([None, None, None])
                poly = []
                for pt in range(last_occurence, len(drawPolygon)):
                    poly.append(drawPolygon[pt])
                if len(poly) > 1:
                    DrawToolBar.drawPolygonOnVideo(
                        poly, painter, surface, gt)
            else:
                DrawToolBar.drawPolygonOnVideo(
                    drawPolygon, painter, surface, gt)

        # Draw Ruler on video
        # the measures don't persist in the video
        if len(drawRuler) > 1:
            DrawToolBar.resetRulerDistance()
            for idx, pt in enumerate(drawRuler):
                if pt[0] is None:
                    DrawToolBar.resetRulerDistance()
                    continue
                else:
                    DrawToolBar.drawRulerOnVideo(
                        pt, idx, painter, surface, gt, drawRuler)

        # Draw Censure
        if drawCesure:
            DrawToolBar.drawCensuredOnVideo(painter, drawCesure)
            return

        return

    @staticmethod
    def drawPointOnVideo(number, pt, painter, surface, gt):
        ''' Draw Points on Video '''
        if hasElevationModel():
            pt = GetLine3DIntersectionWithPlane(
                GetSensor(), pt, GetFrameCenter()[2])

        scr_x, scr_y = vut.GetInverseMatrix(
            pt[1], pt[0], gt, surface)

        # don't draw something outside the screen.
        if scr_x < vut.GetXBlackZone(surface) or scr_y < vut.GetYBlackZone(surface):
            return

        if scr_x > vut.GetXBlackZone(surface) + vut.GetNormalizedWidth(surface) or scr_y > vut.GetYBlackZone(surface) + vut.GetNormalizedHeight(surface):
            return

        radius = 10
        center = QPoint(scr_x, scr_y)

        pen = QPen(Qt.red)
        pen.setWidth(radius)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawPoint(center)
        font12 = QFont("Arial", 12, weight=QFont.Bold)
        painter.setFont(font12)
        painter.drawText(center + QPoint(5, -5), str(number))
        return

    @staticmethod
    def drawLinesOnVideo(pt, idx, painter, surface, gt, drawLines):
        ''' Draw Lines on Video '''
        if hasElevationModel():
            pt = GetLine3DIntersectionWithPlane(
                GetSensor(), pt, GetFrameCenter()[2])

        scr_x, scr_y = vut.GetInverseMatrix(
            pt[1], pt[0], gt, surface)

        radius = 3
        radius_pt = 5
        center = QPoint(scr_x, scr_y)

        pen = QPen(Qt.yellow)
        pen.setWidth(radius)
        pen.setCapStyle(Qt.RoundCap)
        # pen.setDashPattern([1, 4, 5, 4])

        painter.setPen(pen)

        if len(drawLines) > 1:
            try:
                pt = drawLines[idx + 1]
                if hasElevationModel():
                    pt = GetLine3DIntersectionWithPlane(
                        GetSensor(), pt, GetFrameCenter()[2])
                scr_x, scr_y = vut.GetInverseMatrix(
                    pt[1], pt[0], gt, surface)
                end = QPoint(scr_x, scr_y)
                painter.drawLine(center, end)

                # Draw Start/End Points
                pen = QPen(Qt.white)
                pen.setWidth(radius_pt)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawPoint(center)
                painter.drawPoint(end)

            except Exception:
                None
        return

    @staticmethod
    def drawPolygonOnVideo(values, painter, surface, gt):
        ''' Draw Polygons on Video '''
        poly = []
        for pt in values:
            if hasElevationModel():
                pt = GetLine3DIntersectionWithPlane(
                    GetSensor(), pt, GetFrameCenter()[2])
            scr_x, scr_y = vut.GetInverseMatrix(
                pt[1], pt[0], gt, surface)
            center = QPoint(scr_x, scr_y)
            poly.append(center)

        poly.append(poly[0])

        radius = 3
        polygon = QPolygonF(poly)
        pen = QPen()
        pen.setColor(Qt.green)
        pen.setWidth(radius)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        brush = QBrush()
        brush.setColor(QColor(176, 255, 128, 28))
        brush.setStyle(Qt.SolidPattern)

        path = QPainterPath()
        path.addPolygon(polygon)

        painter.setPen(pen)
        painter.drawPolygon(polygon)
        painter.fillPath(path, brush)
        return

    @staticmethod
    def resetRulerDistance():
        global RulerTotalMeasure
        RulerTotalMeasure = 0.0

    @staticmethod
    def drawRulerOnVideo(pt, idx, painter, surface, gt, drawRuler):
        ''' Draw Ruler on Video '''
        if hasElevationModel():
            pt = GetLine3DIntersectionWithPlane(
                GetSensor(), pt, GetFrameCenter()[2])

        scr_x, scr_y = vut.GetInverseMatrix(
            pt[1], pt[0], gt, surface)

        center_pt = pt

        radius_pt = 5
        center = QPoint(scr_x, scr_y)

        if len(drawRuler) > 1:
            try:
                pen = QPen(Qt.red)
                pen.setWidth(3)
                painter.setPen(pen)

                end_pt = drawRuler[idx + 1]

                if hasElevationModel():
                    end_pt = GetLine3DIntersectionWithPlane(
                        GetSensor(), end_pt, GetFrameCenter()[2])
                scr_x, scr_y = vut.GetInverseMatrix(
                    end_pt[1], end_pt[0], gt, surface)
                end = QPoint(scr_x, scr_y)
                painter.drawLine(center, end)

                font12 = QFont("Arial", 12, weight=QFont.Bold)
                painter.setFont(font12)

                distance = round(sphere.distance(
                    (center_pt[0], center_pt[1]), (end_pt[0], end_pt[1])), 2)

                text = str(distance) + " m"
                global RulerTotalMeasure
                RulerTotalMeasure += distance

                # Draw Start/End Points
                pen = QPen(Qt.white)
                pen.setWidth(radius_pt)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawPoint(center)
                painter.drawPoint(end)

                painter.drawText(end + QPoint(5, -5), text)

                pen = QPen(QColor(255, 51, 153))
                painter.setPen(pen)
                painter.drawText(end + QPoint(5, 10),
                                 str(round(RulerTotalMeasure, 2)) + " m")

            except Exception:
                None
        return

    @staticmethod
    def drawCensuredOnVideo(painter, drawCesure):
        ''' Draw Censure on Video '''
        try:
            for geom in drawCesure:
                pen = QPen(Qt.black)
                pen.setWidth(3)
                brush = QBrush()
                brush.setColor(QColor(0, 0, 0))
                brush.setStyle(Qt.SolidPattern)
                painter.setBrush(brush)
                painter.setPen(pen)
                painter.drawRect(geom[0].x(), geom[0].y(),
                                 geom[0].width(), geom[0].height())
        except Exception:
            None
        return

    @staticmethod
    def drawMagnifierOnVideo(widget , dragPos, image, painter):
        ''' Draw Magnifier on Video '''
        print (" imagen : " + str(image.width()) + "  " +str(image.height()))
        
        dim = min(image.width(), image.height())
        magnifierSize = min(DrawToolBar.MAX_MAGNIFIER, dim * 2 / 3)
        radius = magnifierSize / 2
        ring = radius - 15
        box = QSize(magnifierSize, magnifierSize)
        #print (" magnifierSize : " + str(magnifierSize))

        center = dragPos - QPoint(0, radius)
        center += QPoint(0, radius / 2)
        corner = center - QPoint(radius, radius)
        xy = center * 2 - QPoint(radius, radius)

        zoomPixmap = QPixmap(image.width(), image.height())
        print (" box : " + str(box.width()) + "  " +str(box.height()))

        painter_p = QPainter(zoomPixmap)
        #painter_p.translate(-xy)
        painter_p.translate(0, -widget.height())
        painter_p.drawImage(corner, image)
        painter_p.end()
        print (" zoomPixmap : " + str(zoomPixmap.width()) + "  " +str(zoomPixmap.height()))

        clipPath = QPainterPath()
        clipPath.addEllipse(QPointF(center), ring, ring)
        painter.setClipPath(clipPath)
        print (" corner : " + str(corner.x()) + "  " +str(corner.y()))
        painter.drawPixmap(corner, zoomPixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(192, 192, 192, 128), 6))
        painter.drawPath(clipPath)
        return
