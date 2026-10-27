#property strict
#property version "1.10"
#property description "Read-only chart observer. No order execution, network, DLLs or credentials."

input int IntervalSeconds=30;
input bool CaptureScreenshots=true;
input int MaxObjects=1000;
input int MaxIndicatorBuffers=8;
input bool ExportEconomicCalendar=true;
input int CalendarIntervalSeconds=300;
datetime LastCalendarExport=0;

string CalendarNumber(long value)
{
   if(value==LONG_MIN) return "null";
   return DoubleToString((double)value/1000000.0,6);
}

void ExportCalendar()
{
   datetime utc=TimeGMT(),server=TimeTradeServer();
   long offset=(long)(server-utc);
   datetime begin=server-86400,until=server+7*86400;
   string currencies[]={"USD","EUR","GBP","PLN"};
   string events="[",errors="[";
   bool first=true,firstError=true,complete=true;
   for(int c=0;c<ArraySize(currencies);c++)
   {
      MqlCalendarValue values[];
      ResetLastError();
      int count=CalendarValueHistory(values,begin,until,NULL,currencies[c]);
      int error=GetLastError();
      if(count<0 || error!=0)
      {
         complete=false;
         if(!firstError) errors+=",";
         firstError=false;
         errors+="{\"currency\":"+Quote(currencies[c])+",\"code\":"+(string)error+"}";
         continue;
      }
      for(int n=0;n<count;n++)
      {
         MqlCalendarEvent event;
         if(!CalendarEventById(values[n].event_id,event)) { complete=false; continue; }
         bool exact=(event.time_mode==CALENDAR_TIMEMODE_DATETIME);
         long start=(long)values[n].time-offset,end=start;
         if(!exact)
         {
            // Unknown/whole-day time blocks the entire SERVER calendar date.
            start=((long)values[n].time/86400)*86400-offset;
            end=start+86400;
         }
         if(!first) events+=",";
         first=false;
         events+="{\"id\":"+Quote((string)values[n].id)+",\"event_id\":"+Quote((string)event.id);
         events+=",\"name\":"+Quote(event.name)+",\"currency\":"+Quote(currencies[c]);
         events+=",\"importance\":"+(string)(int)event.importance+",\"precision\":"+Quote(exact ? "exact" : "day");
         events+=",\"start_utc\":"+(string)start+",\"end_utc\":"+(string)end;
         events+=",\"source_url\":"+Quote(event.source_url)+",\"unit\":"+Quote(EnumToString(event.unit));
         events+=",\"multiplier\":"+Quote(EnumToString(event.multiplier));
         events+=",\"actual\":"+CalendarNumber(values[n].actual_value)+",\"forecast\":"+CalendarNumber(values[n].forecast_value);
         events+=",\"previous\":"+CalendarNumber(values[n].prev_value)+"}";
      }
   }
   events+="]"; errors+="]";
   string data="{\"schema_version\":\"1.0\",\"source\":\"MT5 Economic Calendar\",\"read_only\":true";
   data+=",\"status\":"+Quote(complete ? "OK" : "UNAVAILABLE")+",\"retrieved_at_utc\":"+(string)(long)utc;
   data+=",\"coverage_from_utc\":"+(string)((long)begin-offset)+",\"coverage_until_utc\":"+(string)((long)until-offset);
   data+=",\"account_login\":"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+",\"account_server\":"+Quote(AccountInfoString(ACCOUNT_SERVER));
   data+=",\"server_minus_gmt_seconds\":"+(string)offset+",\"currencies\":[\"USD\",\"EUR\",\"GBP\",\"PLN\"]";
   data+=",\"events\":"+events+",\"errors\":"+errors+"}";
   string path="TradingAI\\calendar_"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+".json";
   int file=FileOpen(path+".tmp",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(file==INVALID_HANDLE) { Print("Calendar export FileOpen error ",GetLastError()); return; }
   FileWriteString(file,data); FileFlush(file); FileClose(file);
   if(!FileMove(path+".tmp",0,path,FILE_REWRITE)) Print("Calendar export FileMove error ",GetLastError());
   LastCalendarExport=utc;
}

string Quote(string value)
{
   StringReplace(value,"\\","\\\\");
   StringReplace(value,"\"","\\\"");
   StringReplace(value,"\r","\\r");
   StringReplace(value,"\n","\\n");
   StringReplace(value,"\t","\\t");
   return "\""+value+"\"";
}

string Numeric(double value)
{
   if(!MathIsValidNumber(value) || value==EMPTY_VALUE) return "null";
   return DoubleToString(value,10);
}

string ObjectsJson(long chart)
{
   string text="[";
   int count=MathMin(ObjectsTotal(chart,-1,-1),MaxObjects);
   for(int n=0;n<count;n++)
   {
      string name=ObjectName(chart,n,-1,-1);
      if(n>0) text+=",";
      text+="{\"name\":"+Quote(name)+",\"type\":"+(string)ObjectGetInteger(chart,name,OBJPROP_TYPE);
      text+=",\"text\":"+Quote(ObjectGetString(chart,name,OBJPROP_TEXT))+",\"anchors\":[";
      for(int p=0;p<3;p++)
      {
         if(p>0) text+=",";
         double price=0;
         long at=0;
         bool hasPrice=ObjectGetDouble(chart,name,OBJPROP_PRICE,p,price);
         bool hasTime=ObjectGetInteger(chart,name,OBJPROP_TIME,p,at);
         text+="{\"price\":"+(hasPrice ? Numeric(price) : "null")+",\"broker_time\":"+(hasTime ? (string)at : "null")+"}";
      }
      text+="]}";
   }
   return text+"]";
}

string IndicatorsJson(long chart)
{
   string text="[";
   bool first=true;
   int windows=(int)ChartGetInteger(chart,CHART_WINDOWS_TOTAL);
   for(int w=0;w<windows;w++)
   {
      int count=ChartIndicatorsTotal(chart,w);
      for(int n=0;n<count;n++)
      {
         string name=ChartIndicatorName(chart,w,n);
         int handle=ChartIndicatorGet(chart,w,name);
         if(!first) text+=",";
         first=false;
         text+="{\"name\":"+Quote(name)+",\"window\":"+(string)w+",\"closed_bar_shift\":1,\"buffers\":[";
         for(int b=0;b<MaxIndicatorBuffers;b++)
         {
            if(b>0) text+=",";
            double values[1];
            int copied=handle==INVALID_HANDLE ? -1 : CopyBuffer(handle,b,1,1,values);
            text+=copied==1 ? Numeric(values[0]) : "null";
         }
         if(handle!=INVALID_HANDLE) IndicatorRelease(handle);
         text+="]}";
      }
   }
   return text+"]";
}

void ExportChart(long chart)
{
   string suffix=(string)AccountInfoInteger(ACCOUNT_LOGIN)+"_"+(string)chart;
   string name="TradingAI\\observer_"+suffix+".json";
   string screenshot="TradingAI\\chart_"+(string)chart+".png";
   bool captured=false;
   if(CaptureScreenshots) captured=ChartScreenShot(chart,screenshot,1280,720,ALIGN_RIGHT);
   string json="{\"schema_version\":\"1.0\",\"read_only\":true,\"utc_time\":"+(string)(long)TimeGMT();
   json+=",\"account_login\":"+(string)AccountInfoInteger(ACCOUNT_LOGIN)+",\"account_server\":"+Quote(AccountInfoString(ACCOUNT_SERVER));
   json+=",\"broker_server_time\":"+(string)(long)TimeTradeServer()+",\"server_minus_gmt_seconds\":"+(string)(long)(TimeTradeServer()-TimeGMT());
   json+=",\"chart_id\":"+Quote((string)chart)+",\"symbol\":"+Quote(ChartSymbol(chart));
   json+=",\"timeframe\":"+Quote(EnumToString(ChartPeriod(chart)))+",\"screenshot\":"+(captured ? Quote(screenshot) : "null");
   json+=",\"objects\":"+ObjectsJson(chart)+",\"indicators\":"+IndicatorsJson(chart)+"}";
   int file=FileOpen(name+".tmp",FILE_WRITE|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(file==INVALID_HANDLE) { Print("TradingAI observer FileOpen error ",GetLastError()); return; }
   FileWriteString(file,json);
   FileFlush(file);
   FileClose(file);
   if(!FileMove(name+".tmp",0,name,FILE_REWRITE)) Print("TradingAI observer FileMove error ",GetLastError());
}

int OnInit()
{
   if(IntervalSeconds<5 || MaxObjects<0 || MaxObjects>10000 || MaxIndicatorBuffers<1 || MaxIndicatorBuffers>64 || CalendarIntervalSeconds<30)
      return INIT_PARAMETERS_INCORRECT;
   FolderCreate("TradingAI");
   if(!EventSetTimer(IntervalSeconds)) return INIT_FAILED;
   return INIT_SUCCEEDED;
}

void OnTimer()
{
   for(long chart=ChartFirst();chart!=-1;chart=ChartNext(chart)) ExportChart(chart);
   if(ExportEconomicCalendar && TimeGMT()-LastCalendarExport>=CalendarIntervalSeconds) ExportCalendar();
}

void OnDeinit(const int reason) { EventKillTimer(); }
