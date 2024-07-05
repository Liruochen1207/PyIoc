import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Type

from pygments.lexers import q

from PyBean.bean import *
from PyBean.by import *


def boolAttr(inp: str):
    if inp.lower() == 'true' or inp == "1":
        return True
    elif inp.lower() == 'false' or inp == "0":
        return False
    else:
        raise ValueError("Invalid bool input")


def matchBrackets(inp: str):
    state = 0
    front = ""
    end = ""
    if "{" in inp or "}" in inp:
        state += 1
    if "[" in inp or "]" in inp:
        state += 1

    if state > 1:
        raise ValueError("Invalid brackets")
    if "{" in inp:
        front = "{"
        end = "}"
    elif "[" in inp:
        front = "["
        end = "]"
    SPLIT = inp.split(',')
    args = []
    for br in SPLIT:
        tips = 0
        cache = ""
        head = False
        tail = False
        ready = ""
        for s in br:
            cache += s
            if s == front:
                head = True
                continue
            if s == end:
                tail = True
                break
            if head:
                ready += s
        if (not head) and (not tail):
            ready = cache.strip()
        elif (head and tail):
            if front == "{":
                tips = 1
            if front == "[":
                tips = 2
        else:
            tips = -1
        if ready.isdigit():
            ready = float(ready)
        if ready == "true":
            ready = True
        if ready == "false":
            ready = False
        args.append((ready, tips))
    return args


class FuncStringLoader:
    def __init__(self, string: str = ""):
        self.string = string
        self.functionName = ""

    def setString(self, string: str):
        self.string = string

    def load(self):
        print(self.string)
        if self.string:
            return eval(self.string)
        else:
            raise ValueError("No string input")


class ElementLoader:
    def __init__(self, element: ET.Element):
        self.element: ET.Element = element
        self.parent = None
        self.children = []

    def setParent(self, parent):  # parent is a ElementLoader
        self.parent = parent

    def addChild(self, child):  # child is a ElementLoader
        self.children.append(child)


def getAttributeFromElement(element: ET.Element, name: str):
    attribute = element.attrib
    if name in attribute:
        return attribute[name]
    return None


class ApplicationMode:
    release = 0
    default = 1
    development = 2
    debug = 3
    test = 4

    def parse_mode(self, inp: str):
        if inp.isdigit():
            return int(inp)
        if inp.lower() == 'release':
            return self.release
        if inp.lower() == 'default':
            return self.default
        if inp.lower() in ('dev', 'development'):
            return self.development
        if inp.lower() == 'debug':
            return self.debug
        if inp.lower() == 'test':
            return self.test


class ApplicationContext:
    def __init__(self, applicationContextPath: str, applicationMode=ApplicationMode.default):

        applicationContextPath = os.path.abspath(applicationContextPath)
        self.dirPath = os.path.dirname(applicationContextPath)

        self.tree = None
        self.root = None
        self.pointer = None
        self.depth = None
        self.__scanDiction = None
        f"""
        The none-variables init in {self.reloadFromfile} and {self.refresh}
        """

        self.childApplications = []
        self.__mode = applicationMode
        self.path = applicationContextPath
        self.reloadAll()
        self.__doImportLoadList()

    def set__mode(self, mode: ApplicationMode):
        self.__mode = mode

    def debug_print(self, *args, **kwargs):
        if self.__mode in (ApplicationMode.debug, ApplicationMode.test, ApplicationMode.development):
            print(self.path.split('\\')[-1] + " -> ", end='')
            print(*args, **kwargs)

    def pointerLength(self) -> int:
        return self.pointer.__len__()

    def pointerHasChildren(self) -> bool:
        return self.pointerLength() > 0

    def getPointerChildren(self) -> List[ET.Element]:
        li = []
        for index in range(self.pointerLength()):
            li.append(self.pointer[index])
        return li

    def refresh(self):
        self.debug_print('refresh')
        self.__scanDiction: Dict[int, List[ElementLoader]] = self.__scan()

    def reloadFromfile(self):
        self.debug_print('reloadFromfile')
        self.tree: ET.ElementTree = ET.parse(self.path)
        self.root = self.tree.getroot()
        self.pointer: ET.Element = self.root
        self.depth = -1

    def reloadAll(self):
        self.reloadFromfile()
        self.refresh()

    def __scan(self) -> Dict[int, List[ElementLoader]]:
        layer = {}
        rootElementLoader = ElementLoader(self.pointer)
        self.__innerScan(layer, rootElementLoader)
        self.depth = -1
        return layer

    def __innerScan(self, layer: Dict[int, List[ElementLoader]], previousElementLoader: ElementLoader):
        if self.pointerHasChildren():
            self.depth += 1
            for child in self.getPointerChildren():
                childElementLoader = ElementLoader(child)
                childElementLoader.setParent(previousElementLoader)
                previousElementLoader.addChild(childElementLoader)
                if self.depth in layer.keys():
                    layer[self.depth].append(childElementLoader)
                else:
                    layer[self.depth] = [childElementLoader]
                self.pointer = child
                self.__innerScan(layer, childElementLoader)
            self.depth -= 1

    def getScanDiction(self) -> Dict[int, List[ElementLoader]]:
        return self.__scanDiction

    def __getLoaderList(self, depth: int, tagName: str) -> List[ElementLoader]:
        li = []
        if depth in self.getScanDiction():
            for elementLoader in self.getScanDiction()[depth]:
                if elementLoader.element.tag == tagName:
                    li.append(elementLoader)
        return li

    def getImportLoadList(self) -> List[ElementLoader]:
        return self.__getLoaderList(depth=0, tagName='import')

    def __doImportLoadList(self):
        for loader in self.getImportLoadList():
            element = loader.element

            resource = getAttributeFromElement(element, 'resource')
            readyPath = self.dirPath + "\\" + resource
            if not os.path.exists(readyPath):
                readyPath = resource
            childApplication = ApplicationContext(applicationContextPath=readyPath, applicationMode=self.__mode)
            self.childApplications.append(childApplication)

    def getBeanLoaderList(self) -> List[ElementLoader]:
        li = []
        for childApplication in self.childApplications:
            li.extend(childApplication.getBeanLoaderList())
        li.extend(self.__getLoaderList(depth=0, tagName="bean"))
        return li

    def buildRef(self, refLoader: ElementLoader):  # ready for replace
        ref_name = refLoader.element.text
        for childLoader in refLoader.children:
            tag = childLoader.element.tag
            text = childLoader.element.text
            if tag == "ref":
                ref_name = text
                break

        if ref_name is not None:
            # 从ApplicationContext中获取指定名称的Bean
            return self.getBean(ref_name)
        else:
            raise ValueError("No ref name found for <ref/> tag.")


    def buildProperties(self, propsLoader: ElementLoader):
        propInstance = Properties()
        for childLoader in propsLoader.children:
            tag = childLoader.element.tag
            text = childLoader.element.text
            if tag == "prop":
                key = childLoader.element.attrib['key']
                if childLoader.children == []:
                    propInstance.set_property(key, value_translate(text))
                else:
                    for grandchild in childLoader.children:
                        if grandchild.element.tag == "ref":
                            propInstance.set_property(key, self.buildRef(grandchild))

        return propInstance

    def buildCollection_List(self, listLoader: ElementLoader):
        listInstance = []
        for childLoader in listLoader.children:
            tag = childLoader.element.tag

            if tag == "value":
                text = childLoader.element.text
                arg = value_translate(text)
                listInstance.append(arg)
            if tag == "ref":
                arg = self.buildRef(childLoader)
                listInstance.append(arg)

        return listInstance

    def buildCollection_Set(self, setLoader: ElementLoader):
        setInstance = set()
        for childLoader in setLoader.children:
            tag = childLoader.element.tag
            text = childLoader.element.text
            if tag == "value":
                arg = value_translate(text)
                setInstance.add(arg)
            if tag == "ref":
                arg = self.getBean(text)
                setInstance.add(arg)

        return setInstance

    def buildCollection_Map(self, mapLoader: ElementLoader):
        mapInstance = {}
        for childLoader in mapLoader.children:
            if childLoader.element.tag == "entry":
                key = getAttributeFromElement(childLoader.element, 'key')
                value = getAttributeFromElement(childLoader.element, 'value')
                ref = getAttributeFromElement(childLoader.element, 'ref')
                mapInstance[key] = value_translate(value)
                if ref is not None:
                    mapInstance[key] = self.getBean(ref)
        return mapInstance

    def buildBean(self, loader: ElementLoader):
        bean = Bean()

        id = None
        name = None
        className = None

        element: ET.Element = loader.element
        bean.attrib = element.attrib
        id = getAttributeFromElement(element, 'id')
        name = getAttributeFromElement(element, 'name')
        className = getAttributeFromElement(element, 'class')

        childrenLoaders = loader.children
        args = []
        kwargs = {}
        for childLoader in childrenLoaders:
            childElement: ET.Element = childLoader.element
            if childElement.tag == "constructor-arg":
                if "name" in childElement.attrib:
                    kwargs[childElement.attrib["name"]] = childElement.attrib["value"]
                elif "value" in childElement.attrib:
                    value = childElement.attrib['value']
                    args.append(value_translate(value))

                elif "ref" in childElement.attrib:
                    ref = childElement.attrib['ref']
                    value = self.getBean(ref)
                    args.append(value)

            if childElement.tag == "property":
                pn = getAttributeFromElement(childElement, 'name')
                pf = getAttributeFromElement(childElement, 'ref')
                pv = getAttributeFromElement(childElement, 'value')
                if pf is not None:
                    pv = self.getBean(pf)
                prop = Property(
                    name=pn,
                    value=pv,
                )
                if pf == pv == None:
                    for grandchildLoader in childLoader.children:
                        tag = grandchildLoader.element.tag
                        if tag == "map":
                            mapInstance = self.buildCollection_Map(grandchildLoader)
                            prop = Property(
                                name=pn,
                                value=mapInstance,
                            )
                        if tag == "list":
                            listInstance = self.buildCollection_List(grandchildLoader)
                            prop = Property(
                                name=pn,
                                value=listInstance,
                            )
                        if tag == "set":
                            setInstance = self.buildCollection_Set(grandchildLoader)
                            prop = Property(
                                name=pn,
                                value=setInstance,
                            )

                        if tag == "props":
                            propsInstance = self.buildProperties(grandchildLoader)
                            prop = Property(
                                name=pn,
                                value=propsInstance,
                            )
                bean.add_property(prop)

        try:
            bean.create(className, self, *args, **kwargs)
        except TypeError as e:
            # print(e)
            se = str(e)
            if "missing" in se and "required" in se:
                msg = se + f"\n Maybe you forgot to use <constructor-arg/> or delete this argument from {className}."
                raise TypeError(msg)
            raise e

        return bean

    def getBean(self, id, requiredType: Type = Default) -> object:
        def inner():
            if self.__mode == ApplicationMode.development:
                self.reloadAll()
            li = []
            beanELoader = None
            for beanELoader in self.getBeanLoaderList():
                if id in beanELoader.element.attrib.values():
                    li.append(self.buildBean(beanELoader))
            if len(li) > 1:
                for bean in li:
                    if bean.attrib['id'] == id:
                        return bean.instance
                raise KeyError("Too many results -> " + str(li))
            elif len(li) == 0:
                raise KeyError(f"Get bean result '{id}' not found")
            return li[0].instance

        b = inner()
        errorInBed = SystemError(
            f"Object {b.__class__} in {self.path} \n which bean id:'{id}' maybe is not a {requiredType} object")
        try:
            if requiredType == Default or b.__class__ == requiredType:
                return b
            instanceName = str(b.__class__).split("'")[1]
            requiredName = str(requiredType).split("'")[1]
            if (instanceName in requiredName) or (requiredName in instanceName):
                raise NameError(
                    f"The class name of bean id:'{id}' \n in {self.path} is not clear enough, did you mean: '{requiredType}'?")
        except Exception as e:
            raise errorInBed

        raise errorInBed
