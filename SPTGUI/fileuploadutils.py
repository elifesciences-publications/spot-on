import os,shutil,logging,configimpl,json

#configuration for using pyserver.flowjs in windows o linux
#where to change the path separator
##folderlike=configimpl.config.get('fileconfig','folderlike')
folderlike = "/"
#path where to save the file
tmppath=os.getcwd()+folderlike+'static'+folderlike+'tmpdir'+folderlike
uploadpath=os.getcwd()+folderlike+'static'+folderlike+'upload'+folderlike

def cleantmp(arg0):
    logging.info('cleaning')
    try:
        logging.info('start cleaning the %s folder' % tmppath);
        for f in os.listdir(arg0):
            os.remove(arg0+folderlike+f)
    except:
        logging.info("Exception  while removing %s " % tmppath)
        logging.exception("message")

def createFileFromChunk(filename,chunksize,totalsize,flowTotalChunks):
        total_files=0
        logging.info('total chunks is %s' % flowTotalChunks)
        try:
            if not os.path.exists(tmppath):
                os.makedirs(tmppath)
            for f in os.listdir(tmppath):
                if f.index(filename)!=-1:
                    total_files=total_files+1
            if total_files<1:
                return 'UPLOAD'
        except:
            logging.exception("message")
        logging.info('total files %s ' % str(total_files) )
        if(total_files==1 and int(flowTotalChunks)==1):
            try:
                logging.info('upload path from config %s ' % uploadpath)
                logging.info('completing file %s ' % uploadpath+filename);
                f=open(uploadpath+filename,'wb+')
                newFile=tmppath+filename+'.'+'part1'
                file=open(newFile,'rb');
                try:
                    f.write(file.read())
                except:
                    logging.exception("message")
                file.close()
                f.close()
                logging.info('the total chunks is %s' %str(flowTotalChunks))
                logging.info('in tmppath folder there is %s chunk'%str(total_files))
            except:
                logging.exception("message")
            cleantmp(tmppath)
        #total_files * int(chunksize))>=(int(totalsize)-int(chunksize) + 1
        #this maybe the real check to do
        elif(str(total_files)==flowTotalChunks):
            logging.info('Merging file')
            f=open(uploadpath+filename,'wb')
            logging.info('ending file %s ' % f)
            for i in range(1,total_files+1):
                newFile=tmppath+filename+'.'+'part'+str(i)
                logging.info('reading new file %s' % newFile)
                file=open(newFile,'rb')
                try:
                    f.write(file.read())
                except:
                    logging.exception("message")
                    file.close()
                logging.info('the total chunks is %s' %str(flowTotalChunks))
                logging.info('in tmppath folder there is %s chunk'%str(total_files))
            f.close()
            cleantmp(tmppath)
        else:
            return 'UPLOAD'

def checkValidityFile(request, response):
    """Called with a GET request
    Used to cehck the validity of the file.
    For flow.jf (ng-flow) to proceed, it is compulsory that it receives
    a code 400 HTML response. A 200 code doesn't work."""
    
    logging.info("file checking")

    ## Validations
    flowChunkSize=str(request.GET['flowChunkSize'])
    flowFileName=str(request.GET['flowFilename'])
    flowTotalSize=str(request.GET['flowTotalSize'])
    flowTotalChunks=str(request.GET['flowTotalChunks'])
    flowChunkNumber=str(request.GET['flowChunkNumber'])
    responseTotalChunks={'totalchunks':flowTotalChunks}

    n = json.dumps(responseTotalChunks)
    return (400,n)
        
def chunkOperationUtil(request,response):
    """Handle the POST request"""
    flowFileName=None
    flowChunkSize=None
    flowTotalSize=None
    flowChunkNumber=None
    responseTotalChunks=None

    ## Validate input (throws exception if missing I guess)
    flowChunkNumber=str(request.POST['flowChunkNumber'])
    flowChunkSize=str(request.POST['flowChunkSize'])
    flowFileName=request.POST['flowFilename']
    flowTotalSize=str(request.POST['flowTotalSize'])
    flowTotalChunks=str(request.POST['flowTotalChunks'])
        
    logging.info('uploading file %s \n file info: flowchuncknumber = %s; flowchunksize = %s; flowtotalsize = %s;' % (flowFileName, flowChunkNumber, flowChunkSize, flowTotalSize))
    
    logging.info('creating folder')
    createTempFile(flowFileName,flowChunkNumber,request.FILES['file'].read())
    logging.info("Building file")
    createFileFromChunk(flowFileName,flowChunkSize,flowTotalSize,flowTotalChunks)

    if os.path.isfile(uploadpath+folderlike+flowFileName):
        path=str(uploadpath+flowFileName)
        responseTotalChunks={'msg':'file upload complete',
                             'address':path,
                             'filename':flowFileName}
    else:
        logging.info('file not yet completed %s ' % str(flowChunkNumber))
        
    n = json.dumps(responseTotalChunks)
    return (200, n)


def createTempFile(flowFileName,flowChunkNumber,chunk):
    try:
        logging.info('create %s '% tmppath)
        os.mkdir(tmppath)
    except:
        logging.info(" %s allready exists" % tmppath)
    chunk_file = str(flowFileName)+'.part'+str(flowChunkNumber)
    chunkpath=tmppath+chunk_file
    try:
        chunkFile=open(chunkpath,'wb')
        chunkFile.write(chunk)
        chunkFile.close()
        logging.info('file completed name is %s ' % chunkpath)
    except:
        logging.exception("message")
