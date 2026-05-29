/*
 * stcom.h  
 * contains the station common variables for TIGO.
 * Heavily used by antcn and ACU related commands.
 *
 * WHEN       WHO         WHAT
 * 98-02-18   Hayo Hase   lmjd_d, lutc_s added for event controlled aculoop
 * 97-07-31   Hayo Hase   rx part added for rcx3 mainenance program
 * 97-07-17   Hayo Hase   monan added for antenna pointing monitoring
 * 97-07-14   Hayo Hase   factor added due to shortest way to new source
 * 97-07-11   Hayo Hase   receiver RX variables replaced by sk-stuff, aecho added
 * 97-04-14   Hayo Hase   receiver (RX) variables added
 * 96-09-23   Hayo Hase   inclch1offs, inclch2offs added
 * 96-07-31   Hayo Hase   ipmin/maxazi/ele un-unsigned
 * 96-06-02   Hayo Hase   created
 *
 */

typedef struct stcom {
  int dummy;              /* just a dummy */

/*
 *   Common variables for TIGO ACU-Status (long and short status)
 *   variables are updated by getls.c (L:) getss.c (S:) getmet.c (M:)
 *   getoffs.c (T:) getc.c (C:) and set by setmet.c (M:) setofft.c (T:)
 *   setc.c (C:)
 *   Stringvariables beginning with 's' contain ACU status messages.
 *   AN:  used by antcn
 *   STQ: used by stqkr
 *   AC:  used for ACU communication
 *
 *   When     Who          What
 *   96-07-15 Hayo Hase    Dsazi.drvstop, Dsele.drvstop added
 *   96-06-11 Hayo Hase    extended
 *   96-05-08 Hayo Hase    created
 */
    unsigned char mazi;           /*L:S:   Azimuth Mode                     */
             char smazi[9];       /*L:S:   Azimuth Mode String              */
        long int  azipos;         /*L:S:   Azimuth Position [0.0001 deg]    */
        long int  aziab;          /*L:S:   Azimuth Deviation [0.0001 deg]   */
        long int  aziv;           /*L:     Azimuth Velocity  [0.0001 deg/s] */
    unsigned char aziend;         /*L:     Azimuth Limit Switch             */
             char saziend[29];    /*L:     Azimuth Limit Switch             */
    unsigned char dsazi;          /*L:S:   Azimuth Drive Status             */
  struct {
    unsigned char drv1act;        /*L:S:           Drive 1 active [1=y, 0=n]*/
    unsigned char drv1intl;       /*L:S:           Drive 1 interlock active */
    unsigned char drv1fault;      /*L:S:           Drive 1 fault            */
    unsigned char drv2act;        /*L:S:           Drive 2 active [1=y, 0=n]*/
    unsigned char drv2intl;       /*L:S:           Drive 2 interlock active */
    unsigned char drv2fault;      /*L:S:           Drive 2 fault            */
    unsigned char drvstop;        /*L:S:           Drives run[1] or stop[0] */
             char sdrv1act[17];   /*L:S:           Drive 1 active [1=y, 0=n]*/
             char sdrv1intl[27];  /*L:S:           Drive 1 interlock active */
             char sdrv1fault[17]; /*L:S:           Drive 1 fault            */
             char sdrv2act[17];   /*L:S:           Drive 2 active [1=y, 0=n]*/
             char sdrv2intl[27];  /*L:S:           Drive 2 interlock active */
             char sdrv2fault[17]; /*L:S:           Drive 2 fault            */
             char sdrvstop[12];   /*L:S:           Drives run[1] or stop[0] */
  } Dsazi;
    unsigned char deazi;          /*L:S:   Azimuth Drive Error              */
  struct {
    unsigned char drv1;           /*L:S:           Drive 1 (0 = ok)         */
    unsigned char drv2;           /*L:S:           Drive 2 (0 = ok)         */
             char sdrv1[25];      /*L:S:           Drive 1 Msg              */
             char sdrv2[25];      /*L:S:           Drive 2 Msg              */
  } Deazi;
    unsigned char ssazi;          /*L:     Azimuth Stow Status              */
             char sssazi[19];     /*L:     Azimuth Stow Status              */ 
    unsigned char mele;           /*L:S: Elevation Mode                     */
             char smele[9];       /*L:S: Elevation Mode String              */             
        long int  elepos;         /*L:S: Elevation Position [0.0001 deg]    */
        long int  eleab;          /*L:S: Elevation Deviation [0.0001 deg]   */
        long int  elev;           /*L:   Elevation Velocity [0.0001 deg/s]  */
    unsigned char eleend;         /*L:   Elevation Limit Switch             */
             char seleend[29];    /*L:   Elevation Limit Switch             */
    unsigned char dsele;          /*L:S: Elevation Drive Status             */
  struct {
    unsigned char drv1act;        /*L:S:           Drive 1 active [1=y, 0=n]*/
    unsigned char drv1intl;       /*L:S:           Drive 1 interlock active */
    unsigned char drv1fault;      /*L:S:           Drive 1 fault            */
    unsigned char drv2act;        /*L:S:           Drive 2 active [1=y, 0=n]*/
    unsigned char drv2intl;       /*L:S:           Drive 2 interlock active */
    unsigned char drv2fault;      /*L:S:           Drive 2 fault            */
    unsigned char drvstop;        /*L:S:           Drives run[1] or stop[0] */
             char sdrv1act[17];   /*L:S:           Drive 1 active [1=y, 0=n]*/
             char sdrv1intl[27];  /*L:S:           Drive 1 interlock active */
             char sdrv1fault[17]; /*L:S:           Drive 1 fault            */
             char sdrv2act[17];   /*L:S:           Drive 2 active [1=y, 0=n]*/
             char sdrv2intl[27];  /*L:S:           Drive 2 interlock active */
             char sdrv2fault[17]; /*L:S:           Drive 2 fault            */
             char sdrvstop[12];   /*L:S:           Drives run[1] or stop[0] */
  } Dsele;
    unsigned char deele;          /*L:S: Elevation Drive Error              */
  struct {
    unsigned char drv1;           /*L:S:           Drive 1 (0 = ok)         */
    unsigned char drv2;           /*L:S:           Drive 2 (0 = ok)         */
             char sdrv1[25];      /*L:S:           Drive 1 Msg              */
             char sdrv2[25];      /*L:S:           Drive 2 Msg              */
  } Deele;
    unsigned char ssele;          /*L:   Elevation Stow Status              */
             char sssele[19];     /*L:   Elevation Stow Status              */
    unsigned char intst;          /*L:   Interlock Status                   */
             char sintst[28];     /*L:   Interlock Status                   */
    unsigned char emest;          /*L:   Emergency Status                   */
             char semest[33];     /*L:   Emergency Status                   */
    unsigned char control;        /*L:S:   Control Status                   */
  struct {
    unsigned char who;            /*L:S:           Remote (0) or Local (1)  */
    unsigned char stcoord;        /*L:S:           Station Coord. set (1)   */
    unsigned char battery;        /*L:S:           Battery ok (1)           */
    unsigned char freebuff;       /*L:S:           Free Buffer PrgmTrack (1)*/
             char swho[15];       /*L:S:           Remote (0) or Local (1)  */
             char sstcoord[28];   /*L:S:           Station Coord. set (1)   */
             char sbattery[14];   /*L:S:           Battery ok (1)           */
             char sfreebuff[12];  /*L:S:           Free Buffer PrgmTrack (1)*/
  } Control;
    unsigned char commu;          /*L:   Communic. Status */
  struct {
    unsigned char remerr;         /*L:             Remote Interface err (0) */
    unsigned char locerr;         /*L:             Local Panel error (0)    */
    unsigned char dcc;            /*L:             DCC error (0)            */
    unsigned char acc1az;         /*L:             ACC1 azimuth error (0)   */
    unsigned char acc2az;         /*L:             ACC2 azimuth error (0)   */
    unsigned char acc1el;         /*L:             ACC1 elevation error (0) */
    unsigned char acc2el;         /*L:             ACC2 elevation error (0) */
             char sremerr[23];    /*L:             Remote Interface err. (0)*/
             char slocerr[18];    /*L:             Local Panel error (0)    */
             char sdcc[10];       /*L:             DCC error (0)            */
             char sacc1az[19];    /*L:             ACC1 azimuth error (0)   */
             char sacc2az[19];    /*L:             ACC2 azimuth error (0)   */
             char sacc1el[21];    /*L:             ACC1 elevation error (0) */
             char sacc2el[21];    /*L:             ACC2 elevation error (0) */
 } Commu;   
    unsigned long datum;          /*L:S:     Clock Modified Julian Date [d] */
    unsigned long zeit;           /*L:S:     Clock Universal Time Coord [s] */
    unsigned char zeitsrc;        /*L:S:     Clock Time Source              */
             char szeitsrc[32];   /*L:S:     Clock Time Source              */
    unsigned int  space;          /*L: Bufferspace Program Track            */
      signed long ipminazi;       /*L:     Azimuth Min Inp Val [0.0001 deg] */
      signed long ipmaxazi;       /*L:     Azimuth Max Inp Val [0.0001 deg] */
      signed long ipminele;       /*L:   Elevation Min Inp Val [0.0001 deg] */
      signed long ipmaxele;       /*L:   Elevation Max Inp Val [0.0001 deg] */

    unsigned char  inclst;        /*  Inclinometer Status                   */
    unsigned char  inch1;         /*  Inclinometer Channel 1 [enable=1]     */
    unsigned char  inch2;         /*  Inclinometer Channel 2 [disable=0]    */
             char  sinch1[26];    /*  Inclinometer Channel 1 [enable=1]     */
             char  sinch2[26];    /*  Inclinometer Channel 2 [enable=1]     */
      signed long  inclch1;       /*  Inclinometer Channel 1 [deg/incr]     */
      signed long  inclch2;       /*  Inclinometer Channel 2 [deg/incr]     */
      signed long  inclcorr;      /*  Inclinometer norm Average [0.0001deg] */
                                  /*  1 incr = 0.000183 deg                 */
      signed long  inclch1offs;   /*  Inclinometer Ch1. Offset [steps?]     */
      signed long  inclch2offs;   /*  Inclinometer Ch2. Offset [steps?]     */
                                           
      signed long  longit;        /*C:     Station Longitude [0.0001 deg]   */
      signed long  latit;         /*C:     Station Latitude  [0.0001 deg]   */
      signed long  height;        /*C:     Station Height    [m]            */
      signed long  poffaz;        /*C:O:   Azimuth Perm Offset [0.0001 deg] */
      signed long  poffel;        /*C:O: Elevation Perm Offset [0.0001 deg] */ 
      
      signed short temp;          /*M: Temperature Value [0.1 deg C]        */
      signed short humi;          /*M:    Humidity Value [0.1%]             */
      signed short press;         /*M: Airpressure Value [0.1 hPas]         */
    unsigned char  metsrc;        /*M:      Source of metdata               */ 
          
      signed long  toffaz;        /*O:     Azimuth temp offset [0.0001 deg] */
      signed long  toffel;        /*O:   Elevation temp offset [0.0001 deg] */
      signed long  offday;        /*T:O:       Day temp offset [day]        */
      signed long  offsec;        /*T:O:   Seconds temp offset [s]          */

      signed long  aculoop_flag;  /*STQc:ACU=on/off command Securityloop ACU*/
      signed long  aflg;          /*STQf:ACU=on/off command Securityloop ACU*/
      signed long  pgt_flag;      /*AN:    Program Track Flag (=1, 0=Autom.)*/
      signed long  preloop_flag;  /*AN:    Preset  Loop  Flag (=1 no stop)) */
      signed long  azi;           /*AN:    Azimuth commanded (Program Track)*/
      signed long  ele;           /*AN:  Elevation commanded (Program Track)*/  
      signed long  mjd_d;         /*AN:        MJD [day]                    */       
      signed long  utc_s;         /*AN:        UTC [s]                      */       

      signed long  aecho;
             
 #define max_skcodes 64            /*SK: Receiver parameters                 */
 #define max_curve   30            /*    see also ../../st/help/sk.__        */
             float tmpk[max_curve];     
             float pvolt[max_curve];
             float skvfac[max_skcodes];
             float vadcsk;
             int   nsk_curve;
             int   skncodes;
             int   ibxhsk;
             int   iaxhsk;
             int   idchsk;
             int   ifamsk[3];
             int   lostsk;
             int   lcalsk;
             int   valvsk;
             int   pumpsk;
             short iadcsk;
             short sk20k; 
             short sk70k;
             short sklcodes[3][max_skcodes];   /* End of Receiver parameters*/

     signed  long  factor;        /*PG: 1=+360, 0=0, -1=-360 to azimuth cmd.*/       
   unsigned  long  notrkval;      /*PG: number of computed track values     */
   
  struct monan {
       int active;
  } monan;
                             
             float rxtmpk[30];    /*RX: Diode temp. values [K], rxdiode.ctl */
             float rxpvolt[30];   /*RX: Diode volt. values [V], rxdiode.ctl */
             float rxvfac[64];    /*RX: Voltage factors, rxdef.ctl          */
    unsigned char  rxcode[64][7]; /*RX: Code names of A/D channel, rxdef.ctl*/
    unsigned char  rxunit[64][4]; /*RX: physical unit of parameter          */
    unsigned char  rxiadc;        /*RX: A/D channel 00..63                  */
    unsigned char  rxiaux;        /*RX: Aux heat 0/1 = off/on               */
    unsigned char  rxibox;        /*RX: Box heat 0/1 = off/on               */
    unsigned char  rxical;        /*RX: Noise cal 0/1/2 = off/on/ext        */
    unsigned char  rxidcal;       /*RX: Dcal heat 0/1 = on/off              */
    unsigned char  rxifamp[3];    /*RX: S1/X/S2 IF-amplifier 0/1 = off/on   */
    unsigned char  rxiheat;       /*RX: Transition bit 0/1 = off/on         */
    unsigned char  rxilo;         /*RX: LO status 0/1 = unlocked/locked     */
    unsigned char  rxipmp;        /*RX: Vacuum pump 0/1 = off/on            */
    unsigned char  rxireset;      /*RX: LO latch reset switch 0/1 = on/off  */
    unsigned char  rxitrb;        /*RX: Turbo pump 0/1 = off/on             */
    unsigned char  rxival;        /*RX: Vacuum valve 0/1 = closed/open      */
    
             float rx20k;         /*RX: 20K Temperature [K] */
             float rx70k;         /*RX: 70K Temperature [K] */
             float rxpress;       /*RX: Vacuum Press [mmHg] */
             float rxhesup;       /*RX: He Supply Pressure [PSI] */
             float rxhertn;       /*RX: He Supply Return [PSI] */

      signed short wdir;          /*W:  Wind direction [0.1 deg]            */
      signed short wvel;          /*W:  Wind velocity [0.1 m/s]             */  

      signed long  pmoffaz;       /*PM:  Az. point.mod. offset [0.0001 deg] */
      signed long  pmoffel;       /*PM:  El. point.mod. offset [0.0001 deg] */
      signed short pmflag;        /*PM:  Pointing model applied, 0=no,1=yes */

    unsigned long  wmjd_d;        /*W:  last weather record  MJD [day]      */       
    unsigned long  wutc_s;        /*W:  last weather record  UTC [s]        */       

    unsigned long  lmjd_d;        /*AC: last acu command  MJD [day]         */
    unsigned long  lutc_cs;       /*AC: last acu command  UTC [0.01s]       */
    

    	/**************************************************
	ACU Upgrade Section starts here
	**************************************************/

	//General Status
	unsigned int 	acuversion;		//ACU Software Version
	unsigned int	acumaster;		//Control of the ACU
	char		sacumaster[8];		//String control of the ACU
	unsigned int	itrlock1;		//Interlock 1 Indication (Software)
	unsigned int	itrlock2;		//Interlock 2 Indication (Hardware)
	unsigned int	auxlimswitch;		//Aux Limit Switch
	unsigned int	acttimeyear;		//Actual ACU time [year]
	unsigned int	acttimeday;		//Actual ACU time [day of year]
	unsigned int	acttimemsec;		//Actual ACU time [milliseconds of day]
	double		acttimeoffset;		//Actual time offset [seconds.milliseconds]
	unsigned int	trackstatprog;		//Status of program track
	unsigned int	trackerr;		//Error indication for tracking,
	unsigned int	trackwarn;		//Warning indication for tracking,


	//Azimuth Status
	unsigned int	Azstatstatecontrol;	//Status of Azimuth main axis state machine and command execution
	char		sAzstatstatecontrol[14];//String status of Azimuth main axis state machine and command execution
	unsigned int	Azstatposloop;		//Status of Azimuth main axis position loop
	char		sAzstatposloop[10];	//String status of Azimuth main axis position loop
	unsigned int	Azerr;			//Error indication in AZ
	unsigned int	Azwarn;			//Warning indication in AZ
	unsigned int	Azlimitswitch;		//Limit switch indication in AZ
	unsigned int	Azdesrateinput;		//Input source for slewing rates in AZ
	double		Azdesrateslew;		//Desired slewing rate in AZ [deg/s]
	double		Azactposoffset;		//Actual applied position offset in AZ [deg]
	double		Azdespos;		//Desired position from host computer in AZ [deg]
	double		Azcmdpos;		//Commanded position after pre-processing in AZ [deg]
	double		Azactpos;		//Actual position in AZ [deg]
	double		Azactrate;		//Actual rate in AZ [deg]
	int		Azactcurr1;		//Actual current of motor AZ 1 [% of max. current]
	int		Azactcurr2;		//Actual current of motor AZ 2 [% of max. current]
	unsigned int	Azbrakestatus;		//Actual error status of the AZ brakes
	unsigned int	Azmotorerr;		//Actual error status of the AZ motors
	unsigned int	Azmotorwarn;		//Actual warning status of the AZ motors
	unsigned int	Azstatussim;		//Actual AZ simulation status (0 = Off, 1 = Active)
	unsigned int	Azdiagsim;		//Actual AZ diagnostic status (0 = Off, 1 = Active)

	double		Azpmoff;		//Azimuth Offset applied from Pointing Model


	//Elevation Status
	unsigned int	Elstatstatecontrol;	//Status of Elevation main axis state machine and command execution
	char		sElstatstatecontrol[14];//String status of Elevation main axis state machine and command execution
	unsigned int	Elstatposloop;		//Status of Elevation main axis position loop
	char		sElstatposloop[10];	//String status of Elevation main axis position loop
	unsigned int	Elerr;			//Error indication in EL
	unsigned int	Elwarn;			//Warning indication in EL
	unsigned int	Ellimitswitch;		//Limit switch indication in EL
	unsigned int	Eldesrateinput;		//Input source for slewing rates in EL
	double		Eldesrateslew;		//Desired slewing rate in EL [deg/s]
	double		Elactposoffset;		//Actual applied position offset in EL [deg]
	double		Eldespos;		//Desired position from host computer in EL [deg]
	double		Elcmdpos;		//Commanded position after pre-processing in EL [deg]
	double		Elactpos;		//Actual position in EL [deg]
	double		Elactrate;		//Actual rate in EL [deg]
	int		Elactcurr1;		//Actual current of motor EL 1 [% of max. current]
	int		Elactcurr2;		//Actual current of motor EL 2 [% of max. current]
	unsigned int	Elbrakestatus;		//Actual error status of the EL brakes
	unsigned int	Elmotorerr;		//Actual error status of the EL motors
	unsigned int	Elmotorwarn;		//Actual warning status of the EL motors
	unsigned int	Elstatussim;		//Actual EL simulation status (0 = Off, 1 = Active)
	unsigned int	Eldiagsim;		//Actual EL diagnostic status (0 = Off, 1 = Active)

	double		Elpmoff;		//Elevation Offset applied from Pointing Model

	//Tigo Status
	double		permoffaz;		//Permanent offset in Azimuth
	double		permoffel;		//Permanent offset in Elevation
	double		poslimitupaz;		//Position limit up in Azimuth
	double		poslimitupel;		//Position limit up in Elevation
	double		poslimitdoaz;		//Position limit down in Azimuth
	double		poslimitdoel;		//Position limit down in Elevation
	unsigned int	statchan;		//Status of the inclinometer channels
	double		inclactvalue1;		//Actual correction value channel 1
	double		inclactvalue2;		//Actual correction value channel 2
	double		incloffchan1;		//Offset inclinometer channel 1
	double		incloffchan2;		//Offset inclinometer channel 2
	double		antlongitude;		//Longitude of the actual antenna location
	double		antlatitude;		//Latitude of the actual antenna location
	double		antaltitude;		//Altitude of the actual antenna location
	double		anttemp;		//Temperature set by command
	double		anthumi;		//Humidity set by command
	double		antpres;		//Pressure set by command
	unsigned int	acttrackpoint;		//Actual position of the prog track table
	unsigned int	endtrackpoint;		//Last position of the prog track table

	unsigned int	cmd_snumb;		//Next Command Serial Number to Use
	unsigned int	sta_snumb;		//Last Status Serial Number Received

	unsigned int	cmd_con;		//Command Link Engaged
	unsigned int	sta_con;		//Status Link Engaged

	int		aculinkstatus;		//0: ACU Connection Down, 1: ACU Connection OK

        //TIGO Sattrack 
        char   selected_sat[24];// The selected satellite for tracking
        char   activity[20];    // predictict or tracking
        double period;         // period for activity in hours
        double obs_lat;  // Observer position
        double obs_long; // Observer position
        double obs_alt;  // Observer position

        double sattr_az;      // azimuth generated by sattr
        double sattr_el;      // elevation generated by sattr
        double sattr_rg;      // range to the satellite generated by sattr

	/**************************************
	* RX2 Receiver Monitoring starts here *
	**************************************/
	int rx2_con;				//0 if no connection is alive, 1 otherwise

	float rx2_avalue[32];			//Analog channel values, must agree with ANALG_CH of rxcom.h
	float rx2_dvalue[2];			//Digital channel values, must agree with DIGTL_CH of rxcom.h
} Stcom;

