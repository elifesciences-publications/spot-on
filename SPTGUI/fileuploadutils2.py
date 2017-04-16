import os,shutil,logging,json

## TODO: handle tmp files in a better way!

#configuration for using pyserver.flowjs in windows o linux
#where to change the path separator
folderlike='/' #configimpl.config.get('fileconfig','folderlike')
#path where to save the file
tmppath=os.getcwd()+folderlike+'static'+folderlike+'tmpdir'+folderlike
uploadpath=os.getcwd()+folderlike+'static'+folderlike+'upload'+folderlike

def cleantmp(arg0, filename):
    logging.info('cleaning')
    try:
        logging.info('start cleaning the %s folder' % tmppath);
        for f in os.listdir(arg0):
            if f.startswith(filename): ## Wrong, we might remove more than expected
                os.remove(arg0+"/"+f)
            #else:
            #    print "not removing f:", f
    except:
        logging.exception("Exception  while removing %s " % tmppath)
        #logging.exception("message")

def createFileFromChunk(filename,chunksize,totalsize,flowTotalChunks):
        total_files=0
        logging.info('total chunks is %s' % flowTotalChunks)
        try:
            if not os.path.exists(tmppath):
                os.makedirs(tmppath)
            for f in os.listdir(tmppath):
                try:
                    if f.index(filename)!=-1: ## Fails if multiple tmp uploads at the same time
                        total_files=total_files+1
                except:
                    pass 
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
                    logging.exception("Exception while writing the file")
                file.close()
                f.close()
                logging.info('the total chunks is %s' %str(flowTotalChunks))
                logging.info('in tmppath folder there is %s chunk'%str(total_files))
            except:
                logging.exception("message")
            cleantmp(tmppath, filename)
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
                    logging.exception("Screwed in writing the file")
                    file.close()
                logging.info('the total chunks is %s' %str(flowTotalChunks))
                logging.info('in tmppath folder there is %s chunk'%str(total_files))
            f.close()
            cleantmp(tmppath, filename)
        else:
            return 'UPLOAD'

def chunkOperationUtil(request,response):
        flowFileName=None
        flowChunkSize=None
        flowTotalSize=None
        flowChunkNumber=None
        responseTotalChunks=None
        if (request.method == 'GET'):
            #check the validity of the file
            logging.info("file checking")
            flowChunkSize=str(request.args['flowChunkSize'])
            flowFileName=str(request.args['flowFilename'])
            flowTotalSize=str(request.args['flowTotalSize'])
            flowTotalChunks=str(request.args['flowTotalChunks'])
            flowChunkNumber=str(request.args['flowChunkNumber'])
            flowIdentifier=str(request.args['flowIdentifier'])            
            responseTotalChunks={'totalchunks':flowTotalChunks}
            n = json.dumps(responseTotalChunks)
            response.data=n
            response.status='400'
        elif (request.method == 'POST'):
            flowChunkNumber=str(request.form['flowChunkNumber'])
            flowChunkSize=str(request.form['flowChunkSize'])
            flowFileName=request.form['flowFilename']
            flowTotalSize=str(request.form['flowTotalSize'])
            flowTotalChunks=str(request.form['flowTotalChunks'])
            flowIdentifier=str(request.form['flowIdentifier'])
            logging.info('uploading file %s \n file info: flowchuncknumber = %s; flowchunksize = %s; flowtotalsize = %s;' % (flowFileName, flowChunkNumber, flowChunkSize, flowTotalSize))
            logging.info('creating folder')
            createTempFile(flowFileName,flowChunkNumber,request.FILES['file'].read())
            logging.info("Building file")
            createFileFromChunk(flowFileName,flowChunkSize,flowTotalSize,flowTotalChunks)
            if flowTotalChunks==flowChunkNumber:
                response.ok = True                
            response.status="200"
            if os.path.isfile(uploadpath+"/"+flowFileName):
                path=str(uploadpath+flowFileName)
                responseTotalChunks={'msg':'file upload complete',
                                     'address':path,
                                     'filename':flowFileName,
                                     'unique_id': flowIdentifier
                                 }
            else:
                logging.info('file not yet completed %s ' % str(flowChunkNumber))
            n = json.dumps(responseTotalChunks)
            response.data=n

def createTempFile(flowFileName,flowChunkNumber,chunk):
    try:
        logging.info('create %s '% tmppath)
        os.mkdir(tmppath)
    except:
        logging.info(" %s allready exists" % tmppath)
    chunk_file = str(flowFileName)+'.part'+str(flowChunkNumber)
    chunkpath=tmppath+chunk_file
    #try:
    chunkFile=open(chunkpath,'wb')
    chunkFile.write(chunk)
    chunkFile.close()
    logging.info('file completed name is %s ' % chunkpath)
    #except Exception:
    #    raise
    #    logging.exception("message")
