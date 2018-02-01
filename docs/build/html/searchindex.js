Search.setIndex({docnames:["index","modules","src","src.configuration","src.openstack_api","src.routing","src.routing.API","src.sqlalchemy","src.threads","src.utils"],envversion:53,filenames:["index.rst","modules.rst","src.rst","src.configuration.rst","src.openstack_api.rst","src.routing.rst","src.routing.API.rst","src.sqlalchemy.rst","src.threads.rst","src.utils.rst"],objects:{"":{src:[2,0,0,"-"]},"src.configuration":{config:[3,0,0,"-"]},"src.configuration.config":{Configuration:[3,1,1,""]},"src.openstack_api":{openstackApi:[4,0,0,"-"]},"src.openstack_api.openstackApi":{OpenStackConnector:[4,1,1,""]},"src.openstack_api.openstackApi.OpenStackConnector":{deleteImageByName:[4,2,1,""],findImageIdByName:[4,2,1,""],getAllBibiCreatorImages:[4,2,1,""],getAllImages:[4,2,1,""],getBibiCreatorImagesByUser:[4,2,1,""],getImageByID:[4,2,1,""],isValidConnection:[4,2,1,""]},"src.routing":{API:[6,0,0,"-"],rest:[5,0,0,"-"],views:[5,0,0,"-"]},"src.routing.API":{administratorTools:[6,0,0,"-"],authentication:[6,0,0,"-"],history:[6,0,0,"-"],jobManagement:[6,0,0,"-"],moduleManagement:[6,0,0,"-"],openStack:[6,0,0,"-"],playlists:[6,0,0,"-"],userManagement:[6,0,0,"-"]},"src.routing.API.administratorTools":{getHealth:[6,3,1,""],getVersions:[6,3,1,""],isAdmin:[6,3,1,""]},"src.routing.API.authentication":{getAuthCookie:[6,3,1,""]},"src.routing.API.history":{deleteHistoryByID:[6,3,1,""],getBackupHistoryByID:[6,3,1,""],getHistory:[6,3,1,""],getHistoryLogByID:[6,3,1,""],getHistoryModuleByID:[6,3,1,""],getHistoryModuleFileByID:[6,3,1,""],isAdmin:[6,3,1,""],updateHistoryComment:[6,3,1,""]},"src.routing.API.jobManagement":{getCrashLog:[6,3,1,""],getJobs:[6,3,1,""],isAdmin:[6,3,1,""],removeJobByID:[6,3,1,""],requestNewBuild:[6,3,1,""],requestNewBuildFromPlaylist:[6,3,1,""]},"src.routing.API.moduleManagement":{deleteModuleByID:[6,3,1,""],getFileByID:[6,3,1,""],getForcedModules:[6,3,1,""],getGalaxySearchResult:[6,3,1,""],getModuleByID:[6,3,1,""],getOwnModules:[6,3,1,""],getPublicModules:[6,3,1,""],isAdmin:[6,3,1,""],uploadModule:[6,3,1,""]},"src.routing.API.openStack":{changeBaseImgByID:[6,3,1,""],deleteOSImageByName:[6,3,1,""],getOSIDFromOSName:[6,3,1,""],getOSImages:[6,3,1,""],isAdmin:[6,3,1,""]},"src.routing.API.playlists":{addGalaxyRoleToPlaylist:[6,3,1,""],addModuleToPlaylist:[6,3,1,""],deletePlaylistByID:[6,3,1,""],getPlaylists:[6,3,1,""],isAdmin:[6,3,1,""],registerNewPlaylist:[6,3,1,""],removeModulesFromPlaylist:[6,3,1,""],updatePlaylistDescription:[6,3,1,""]},"src.routing.API.userManagement":{changeUserPassword:[6,3,1,""],createUser:[6,3,1,""],deleteUser:[6,3,1,""],getUserImageLimit:[6,3,1,""],getUsers:[6,3,1,""],isAdmin:[6,3,1,""],updateUser:[6,3,1,""]},"src.routing.rest":{isAdmin:[5,3,1,""],testroute:[5,3,1,""]},"src.routing.views":{cloud_connection:[5,3,1,""],createImage:[5,3,1,""],history_overview:[5,3,1,""],homepage:[5,3,1,""],login_page:[5,3,1,""],logout:[5,3,1,""],manageModules:[5,3,1,""],playlistEditor:[5,3,1,""],playlists:[5,3,1,""],resourceAndHealth:[5,3,1,""],showHistoryByID:[5,3,1,""],userManagement:[5,3,1,""],user_settings:[5,3,1,""]},"src.sqlalchemy":{db_alchemy:[7,0,0,"-"],db_model:[7,0,0,"-"]},"src.sqlalchemy.db_model":{History:[7,1,1,""],HistoryModules:[7,1,1,""],Jobs:[7,1,1,""],Modules:[7,1,1,""],Playlists:[7,1,1,""],Users:[7,1,1,""]},"src.sqlalchemy.db_model.History":{base_image_id:[7,4,1,""],commentary:[7,4,1,""],date:[7,4,1,""],debug_file_path:[7,4,1,""],id:[7,4,1,""],isReady:[7,4,1,""],modules:[7,4,1,""],name:[7,4,1,""],new_image_id:[7,4,1,""],owner:[7,4,1,""],serialize:[7,4,1,""]},"src.sqlalchemy.db_model.HistoryModules":{date:[7,4,1,""],description:[7,4,1,""],id:[7,4,1,""],isForced:[7,4,1,""],module_type:[7,4,1,""],name:[7,4,1,""],owner:[7,4,1,""],path:[7,4,1,""],serialize:[7,4,1,""],version:[7,4,1,""]},"src.sqlalchemy.db_model.Jobs":{base_image_id:[7,4,1,""],date:[7,4,1,""],debug_file_path:[7,4,1,""],id:[7,4,1,""],modules:[7,4,1,""],name:[7,4,1,""],new_image_id:[7,4,1,""],owner:[7,4,1,""],progression:[7,4,1,""],serialize:[7,4,1,""],status:[7,4,1,""]},"src.sqlalchemy.db_model.Modules":{date:[7,4,1,""],description:[7,4,1,""],id:[7,4,1,""],isForced:[7,4,1,""],isPrivate:[7,4,1,""],module_type:[7,4,1,""],name:[7,4,1,""],owner:[7,4,1,""],path:[7,4,1,""],serialize:[7,4,1,""],version:[7,4,1,""]},"src.sqlalchemy.db_model.Playlists":{date:[7,4,1,""],description:[7,4,1,""],id:[7,4,1,""],modules:[7,4,1,""],name:[7,4,1,""],owner:[7,4,1,""],serialize:[7,4,1,""]},"src.sqlalchemy.db_model.Users":{email:[7,4,1,""],id:[7,4,1,""],max_images:[7,4,1,""],name:[7,4,1,""],password:[7,4,1,""],policy:[7,4,1,""],serialize:[7,4,1,""]},"src.threads":{cleanUpThread:[8,0,0,"-"],integrityThread:[8,0,0,"-"],threadManager:[8,0,0,"-"],workerThread:[8,0,0,"-"]},"src.threads.cleanUpThread":{JobCleaner:[8,1,1,""],dirIntegrity:[8,3,1,""]},"src.threads.cleanUpThread.JobCleaner":{run:[8,2,1,""]},"src.threads.integrityThread":{IntegrityCheck:[8,1,1,""]},"src.threads.integrityThread.IntegrityCheck":{run:[8,2,1,""]},"src.threads.threadManager":{ThreadManager:[8,1,1,""]},"src.threads.threadManager.ThreadManager":{checkForTTL:[8,2,1,""],run:[8,2,1,""]},"src.threads.workerThread":{JobWorker:[8,1,1,""],cp_booksAndScripts:[8,3,1,""],cp_booksAndScriptsForced:[8,3,1,""],cp_roles:[8,3,1,""],cp_rolesForced:[8,3,1,""],installFromGalaxy:[8,3,1,""]},"src.threads.workerThread.JobWorker":{run:[8,2,1,""],shutDownPacker:[8,2,1,""]},"src.utils":{backup:[9,0,0,"-"],checkings:[9,0,0,"-"],constants:[9,0,0,"-"],db_connector:[9,0,0,"-"],local_resource:[9,0,0,"-"],packerUtils:[9,0,0,"-"]},"src.utils.backup":{backupEverything:[9,3,1,""]},"src.utils.checkings":{categorizeAndCheckModule:[9,3,1,""],checkNewModuleForm:[9,3,1,""],checkPassedUserFormular:[9,3,1,""],checkToolAvailability:[9,3,1,""]},"src.utils.db_connector":{DB_Connector:[9,1,1,""]},"src.utils.db_connector.DB_Connector":{db:[9,4,1,""],queryAndResult:[9,2,1,""]},"src.utils.local_resource":{get_app_version:[9,3,1,""],get_cpu_load:[9,3,1,""],get_processor_name:[9,3,1,""],get_ram_percent:[9,3,1,""]},"src.utils.packerUtils":{buildPackerJsonFromConfig:[9,3,1,""]},src:{configuration:[3,0,0,"-"],openstack_api:[4,0,0,"-"],routing:[5,0,0,"-"],sqlalchemy:[7,0,0,"-"],threads:[8,0,0,"-"],utils:[9,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","function","Python function"],"4":["py","attribute","Python attribute"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:function","4":"py:attribute"},terms:{"class":[3,4,7,8,9],"default":5,"function":6,"int":6,"long":8,"new":[5,6,8,9],"public":6,"return":[4,6,7,9],"true":[4,6,9],"try":8,"while":6,For:6,Not:8,The:[4,5,6,8,9],Use:6,Uses:6,abl:[6,8],about:6,access:8,account:6,add:6,added:6,addgalaxyroletoplaylist:6,addmoduletoplaylist:6,admin:[5,6],administr:6,after:6,alex:[3,4,5,6,7,8,9],all:[4,5,6,8,9],allow:6,alow:6,alreadi:6,also:[3,6],amdinistr:6,ansibl:[6,8],ansible_roles_path:8,anymor:[6,8],apidoc:6,app:[8,9],applic:6,archiv:[6,9],arg:[],assembl:9,assist:5,attach:6,auth_url:4,authent:5,author:6,autom:[6,9],automat:6,avail:[5,6,9],awalend:[3,4,5,6,7,8,9],backup:6,backupeveryth:9,base:[3,4,5,6,7,8,9],base_image_id:7,bash:[6,8],bck:9,becaus:8,been:4,better:6,bibicr:[3,4,5,6,7,8,9],bibicreator_us:4,bielefeld:[3,4,5,6,7,8,9],blueprint:6,browser:6,build:[6,8],builder:9,buildpackerjsonfromconfig:9,call:[6,9],can:[5,6,8],capabilit:9,categor:9,categorizeandcheckmodul:9,caution:6,cebitec:[3,4,5,6,7,8,9],chang:[5,6],changebaseimgbyid:6,changeuserpassword:6,check:[3,4,5,6,8],checkforttl:8,checknewmoduleform:9,checkpasseduserformular:9,checktoolavail:9,clean:8,cloud_connect:5,code:6,comment:6,commentari:[6,7],comput:[3,4,5,6,7,8,9],configur:[6,9],connect:[4,9],constantli:8,contain:[4,6,7,9],content:1,cooki:6,copi:[6,8],could:8,cp_booksandscript:8,cp_booksandscriptsforc:8,cp_role:8,cp_rolesforc:8,cpu:[5,6,9],crash:6,crashlog:6,creat:[4,6],createimag:5,createus:6,creation:5,curl:6,current:[5,6,8,9],data:5,databas:[7,8,9],date:7,db_pass:9,db_user:9,deadlock:6,debug:6,debug_file_path:7,delet:[4,6],deletehistorybyid:6,deleteimagebynam:4,deletemodulebyid:6,deleteosimagebynam:6,deleteplaylistbyid:6,deletet:6,deleteus:6,deprec:[8,9],describ:6,descript:[6,7],descriptor:8,desir:[4,5,6],detail:9,dict:9,dictionari:[7,9],directori:8,directory_trgt:8,dirintegr:8,disk:6,document:6,doe:6,down:8,download:6,each:6,edit:5,either:5,email:7,endpoint:6,eras:6,error:[6,9],etern:8,everi:6,everytim:6,except:8,execut:9,exist:[6,8],extend:9,fals:[4,8],field:[3,9],file:[3,6,8,9],find:4,findimageidbynam:4,first:5,flask:6,flask_sqlalchemi:7,forc:[6,8],formdict:9,framework:6,from:[4,5,6,8],further:6,galaxi:[6,8],gather:5,gener:6,get:6,get_app_vers:9,get_cpu_load:9,get_processor_nam:9,get_ram_perc:9,getallbibicreatorimag:4,getallimag:4,getauthcooki:6,getbackuphistorybyid:6,getbibicreatorimagesbyus:4,getcrashlog:6,getfilebyid:6,getforcedmodul:6,getgalaxysearchresult:6,gethealth:6,gethistori:6,gethistorylogbyid:6,gethistorymodulebyid:6,gethistorymodulefilebyid:6,getimagebyid:4,getjob:6,getmodulebyid:6,getosidfromosnam:6,getosimag:6,getownmodul:6,getplaylist:6,getpublicmodul:6,getus:6,getuserimagelimit:6,getvers:6,given:4,has:6,have:[4,6],header:6,health:5,henc:6,histori:[5,7],history_overview:5,historyid:5,historymodul:7,homepag:5,host:9,hour:6,http:6,hub:6,imag:[4,5,6,8,9],image_id:4,imageid:[4,6],imagenam:[4,6],imgid:6,incom:9,independendli:6,index:0,inform:[6,9],ini:3,initi:6,input:9,inspect:5,instal:[6,8,9],installfromgalaxi:8,integr:8,integritycheck:8,interact:6,isadmin:[5,6],isforc:7,ispriv:7,isreadi:7,isvalidconnect:4,job:[6,7,8],jobclean:8,jobwork:8,json:[6,9],json_data:9,juvenil:9,kill:6,let:5,link:8,linux:8,list:[4,6,8],live:8,load:9,local:[5,6,8,9],locat:8,lock:8,log:[5,6,8],logfil:[6,8],login:5,login_pag:5,logout:5,lookup:6,loop:8,machin:[5,6,8,9],made:6,manag:[5,8],managemodul:5,manuali:6,max_imag:7,mayb:8,messag:[6,9],met:6,metagenom:[3,4,5,6,7,8,9],model:7,modifi:6,modlist:8,modul:[0,1],module_path:8,module_typ:[7,8],modulefil:6,moduleid:6,more:6,mysql:9,name:[4,6,7,9],need:[3,6],neutron:4,new_image_id:7,none:9,number:[6,9],object:[3,4,6,7,8,9],obtain:[5,6,9],okai:9,onli:[5,6],openstack:[4,8],openstackconnector:4,orm:8,os_image_nam:6,osimagenam:9,output:8,overview:5,own:[4,6],owner:[6,7],packag:1,packer:[6,8,9],page:[0,5],paramet:[4,5,6,8,9],pars:3,parsedini:3,pass:6,password:[4,5,6,7],path:[7,8],percentag:9,person:6,playbook:[6,8],playlist:[5,7],playlisteditor:5,playlistid:[5,6],point:6,polici:7,pop:5,privaci:6,privileg:6,privilig:6,process:[6,8],processor:9,progress:7,project_domain_nam:4,project_nam:4,prompt:6,provid:6,publicli:6,queri:9,queryandresult:9,rais:8,ram:[6,9],receiv:6,record:6,refer:6,registernewplaylist:6,registr:[6,9],regular:6,remov:6,removejobbyid:6,removemodulesfromplaylist:6,render:5,request:6,requestnewbuild:6,requestnewbuildfromplaylist:6,resourceandhealth:5,respons:6,responsibel:8,rest:6,result:6,retreiv:6,role:[6,8],run:[6,8],save:6,script:[6,8,9],sdk:4,search:[0,6],secondstol:8,secur:6,select:6,serial:7,server:[6,9],servic:4,session:[5,6],set:[5,6],shall:[6,8],shell:9,shell_cal:9,should:6,show:6,showhistorybyid:5,shut:8,shutdownpack:8,simpli:6,soft:8,specif:[5,6],specifi:6,spin:8,standard:5,start:6,statement:9,statu:[6,7],still:6,store:6,str:6,success:6,swagger:6,system:[6,8],tag:6,take:8,tar:[6,9],target:[4,5,6,8],targetid:6,tell:6,testrout:5,text:6,thei:[5,6,9],thi:[5,6,8,9],threshold:8,time:8,too:8,tool:[6,9],treat:6,tupl:9,txt:6,type:9,unauthor:6,uni:[3,4,5,6,7,8,9],unix:9,updat:6,updatehistorycom:6,updateplaylistdescript:6,updateus:6,upload:6,uploadmodul:6,uptim:8,url:6,usag:6,use:6,used:[6,8],user:[4,5,6,7,9],user_domain_id:4,user_set:5,userdict:9,userid:6,usermanag:5,usernam:4,uses:6,using:6,valid:[4,6,9],version:[4,6,7,9],via:4,walend:[3,4,5,6,7,8,9],want:6,well:6,were:6,when:6,where:[5,6,8],which:[4,6,8,9],who:6,work:8,worker:8,wrapper:6,yaml:6,yml:6,you:6,your:6},titles:["Welcome to BibiCreator\u2019s documentation!","src","src package","src.configuration package","src.openstack_api package","src.routing package","src.routing.API package","src.sqlalchemy package","src.threads package","src.utils package"],titleterms:{administratortool:6,api:6,authent:6,backup:9,bibicr:0,check:9,cleanupthread:8,config:3,configur:3,constant:9,content:[2,3,4,5,6,7,8,9],db_alchemi:7,db_connector:9,db_model:7,document:0,histori:6,indic:0,integritythread:8,jobmanag:6,local_resourc:9,modul:[2,3,4,5,6,7,8,9],modulemanag:6,openstack:6,openstack_api:4,openstackapi:4,packag:[2,3,4,5,6,7,8,9],packerutil:9,playlist:6,rest:5,rout:[5,6],sqlalchemi:7,src:[1,2,3,4,5,6,7,8,9],submodul:[3,4,5,6,7,8,9],tabl:0,thread:8,threadmanag:8,usermanag:6,util:9,view:5,welcom:0,workerthread:8}})