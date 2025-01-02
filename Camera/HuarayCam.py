import sys
import time
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'MVSDK'))
from Camera.MVSDK.IMVApi import *
import cv2
import numpy
from datetime import datetime
import os

class HuarayCam():
    def __init__(self, args):
        self.args = args
        self.deviceList = IMV_DeviceList()
        self.interfaceType = IMV_EInterfaceType.interfaceTypeAll
        self.cam = MvCamera()
        self.runThread = False
        self.connectionNum = 1
        self.grab_interval = 1.0  # second 단위
        self.dateTime = datetime.now()
        self.secondCount = 0
        self.frame = None
        self.pDstBuf = None  # 전역 변수로 이동

    def setInterval(self, interval):
        self.grab_interval = interval

    def setExposureTime(self, value):
        self.cam.IMV_SetDoubleFeatureValue("ExposureTime", value)

    def setUserOutputValue(self, onoff):
        ret = self.cam.IMV_SetBoolFeatureValue("UserOutputValue", onoff)
        if ret != IMV_OK:
            return -1
        return IMV_OK

    def resetCam(self):
        ret = MvCamera().IMV_EnumDevices(self.deviceList, self.interfaceType)
        if ret != IMV_OK:
            print(f'Enumeration devices failed! ErrorCode : {ret}\n')
            return -1
        if self.deviceList.nDevNum < 1:
            print('no camera\n')
            return -1
        return IMV_OK

    def openCam(self):
        if self.connectionNum > self.deviceList.nDevNum:
            print('Connection Camera Number Error')
            return -1
        ret = self.cam.IMV_CreateHandle(IMV_ECreateHandleMode.modeByIndex, byref(c_void_p(int(self.connectionNum) - 1)))
        if ret != IMV_OK:
            print("Create devHandle failed! ErrorCode", ret)
            return -1
        ret = self.cam.IMV_Open()
        if ret != IMV_OK:
            print("Open devHandle failed! ErrorCode", ret)
        return ret

    def displayDeviceInfo(self):
        #print("Idx  Type   Vendor              Model           S/N                 DeviceUserID    IP Address")
        #print("------------------------------------------------------------------------------------------------")
        for i in range(0, self.deviceList.nDevNum):
            pDeviceInfo = self.deviceList.pDevInfo[i]
            strType = ""
            strVendorName = ""
            strModeName = ""
            strSerialNumber = ""
            strCameraname = ""
            strIpAdress = ""
            for str in pDeviceInfo.vendorName:
                strVendorName = strVendorName + chr(str)
            for str in pDeviceInfo.modelName:
                strModeName = strModeName + chr(str)
            for str in pDeviceInfo.serialNumber:
                strSerialNumber = strSerialNumber + chr(str)
            for str in pDeviceInfo.cameraName:
                strCameraname = strCameraname + chr(str)
            for str in pDeviceInfo.DeviceSpecificInfo.gigeDeviceInfo.ipAddress:
                strIpAdress = strIpAdress + chr(str)
            if pDeviceInfo.nCameraType == typeGigeCamera:
                strType = "Gige"
            elif pDeviceInfo.nCameraType == typeU3vCamera:
                strType = "U3V"
            #print("[%d]  %s   %s    %s      %s     %s           %s" % (i + 1, strType, strVendorName, strModeName, strSerialNumber, strCameraname, strIpAdress))

    def setTrigger(self):
        ret = IMV_OK
        if self.args.trigger_mode == 1:
            ret = self.cam.IMV_SetEnumFeatureSymbol("TriggerSource", "Software")
        else :
            ret = self.cam.IMV_SetEnumFeatureSymbol("TriggerSource", "Line1")

        if ret != IMV_OK:
            print("Set TriggerSource value failed! ErrorCode:", ret)
            return ret

        ret = self.cam.IMV_SetEnumFeatureSymbol("TriggerSelector", "FrameStart")
        if ret != IMV_OK:
            print("Set triggerSelector value failed! ErrorCode", ret)
            return ret

        ret = self.cam.IMV_SetEnumFeatureSymbol("TriggerMode", "On")
        if ret != IMV_OK:
            print("Set triggerMode value failed! ErrorCode:", ret)
            return ret

        if self.args.trigger_mode == 2:
            ret = self.cam.IMV_SetEnumFeatureSymbol("TriggerActivation", "RisingEdge")
            if ret != IMV_OK:
                print("Set Line Trigger type value failed! ErrorCode:", ret)
                return ret

        return ret

    def startGrabbing(self):
        ret = self.cam.IMV_StartGrabbing()
        if ret != IMV_OK:
            print("Start grabbing failed! ErrorCode", ret)
        return ret

    def endGrabbing(self):
        ret = self.cam.IMV_StopGrabbing()
        if ret != IMV_OK:
            print("End grabbing failed! ErrorCode", ret)

    def closeCam(self):
        ret = self.cam.IMV_Close()
        if ret != IMV_OK:
            print("Close cam", ret)

    def get_frame(self): 
        if self.cam.handle == None:
            print('No handle')
            return -1
        self.frame = IMV_Frame()
        ret = -1
        if self.args.trigger_mode == 1:
            ret = self.cam.IMV_ExecuteCommandFeature("TriggerSoftware")
            if ret != IMV_OK:
                print("Execute TriggerSoftware failed! ErrorCode:", ret)
                return -1
        self.cam.IMV_ClearFrameBuffer()
        ret = self.cam.IMV_GetFrame(self.frame, self.args.frame_timeout)
        print('ret', ret)
        if ret != IMV_OK:
            return -1

        return 0

    def release_frame(self):
        ret = self.cam.IMV_ReleaseFrame(self.frame)
        if ret != IMV_OK:
            print('Error type is : Release Error')
            return -1
        return 0

    def executeSoftTriggerProc(self):
        print('execute thread')
        while self.runThread == True:
            if self.args.trigger_mode == 1 :
                self.executeSoftTrigger()
                time.sleep(self.grab_interval)
            elif self.args.trigger_mode == 2 :
                self.executeLineTrigger()

    def getImage(self, frame):
        stPixelConvertParam = IMV_PixelConvertParam()
        if IMV_EPixelType.gvspPixelMono8 == frame.frameInfo.pixelFormat:
            nDstBufSize = frame.frameInfo.width * frame.frameInfo.height
        else:
            nDstBufSize = frame.frameInfo.width * frame.frameInfo.height * 3

        # 기존에 할당된 버퍼가 충분하지 않으면 새로운 버퍼 할당
        if self.pDstBuf is None or len(self.pDstBuf) < nDstBufSize:
            self.pDstBuf = (c_ubyte * nDstBufSize)()

        memset(byref(stPixelConvertParam), 0, sizeof(stPixelConvertParam))

        stPixelConvertParam.nWidth = frame.frameInfo.width
        stPixelConvertParam.nHeight = frame.frameInfo.height
        stPixelConvertParam.ePixelFormat = frame.frameInfo.pixelFormat
        stPixelConvertParam.pSrcData = frame.pData
        stPixelConvertParam.nSrcDataLen = frame.frameInfo.size
        stPixelConvertParam.nPaddingX = frame.frameInfo.paddingX
        stPixelConvertParam.nPaddingY = frame.frameInfo.paddingY
        stPixelConvertParam.eBayerDemosaic = IMV_EBayerDemosaic.demosaicNearestNeighbor
        stPixelConvertParam.eDstPixelFormat = frame.frameInfo.pixelFormat
        stPixelConvertParam.pDstBuf = self.pDstBuf
        stPixelConvertParam.nDstBufSize = nDstBufSize

        if stPixelConvertParam.ePixelFormat == IMV_EPixelType.gvspPixelMono8:
            imageBuff = stPixelConvertParam.pSrcData
            userBuff = c_buffer(b'\0', stPixelConvertParam.nDstBufSize)

            memmove(userBuff, imageBuff, stPixelConvertParam.nDstBufSize)
            grayByteArray = bytearray(userBuff)
            cvImage = numpy.array(grayByteArray).reshape(stPixelConvertParam.nHeight, stPixelConvertParam.nWidth)
        else:
            stPixelConvertParam.eDstPixelFormat = IMV_EPixelType.gvspPixelBGR8
            nRet = self.cam.IMV_PixelConvert(stPixelConvertParam)
            if IMV_OK != nRet:
                print("image convert to failed! ErrorCode[%d]" % nRet)
                return None  # 변환 실패 시 None 반환
            rgbBuff = c_buffer(b'\0', stPixelConvertParam.nDstBufSize)
            memmove(rgbBuff, stPixelConvertParam.pDstBuf, stPixelConvertParam.nDstBufSize)
            colorByteArray = bytearray(rgbBuff)
            cvImage = numpy.array(colorByteArray).reshape(stPixelConvertParam.nHeight, stPixelConvertParam.nWidth, 3)

        return cvImage
