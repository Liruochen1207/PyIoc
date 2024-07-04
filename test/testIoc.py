import time
startTime = time.time()

from typing import List

from PyBean.ioc import ApplicationContext, ApplicationMode, ElementLoader

from test.imp.bookImp import *
importTime = time.time()
def main():
    actx = ApplicationContext('resource/applicationContext.xml',
                              applicationMode=ApplicationMode.release)

    print(actx.getBean("bookImp2", requiredType=BookDaoImp))
    print(actx.getBean("payImp85").discount)
    bookDaoImp: Bookdao = actx.getBean("bookImp")
    bookDaoImp2: Bookdao = actx.getBean("bookImp2")

    print("-" * 50)
    print(bookDaoImp.brotherImp)
    print(bookDaoImp2)
    assert type(bookDaoImp.brotherImp) is type(bookDaoImp2)
    print(actx.getBean("bookImp").myMap)
    print(actx.getBean("bookImp").myList)
    print(actx.getBean("bookImp").mySet)
    print(actx.getBean("bookImp").myProperties)
    print(actx.getBean("bookImp2"))

    print("-" * 50)
    # print(actx.getBeanLoaderList()[0].element.attrib)

if __name__ == '__main__':
    main()
    endTime = time.time()

    print("importTime: %.2f ms" % ((importTime - startTime) * 1000))
    print("Runtime: %.2f ms" % ((endTime - importTime) * 1000))
