for i in 2015 2014 2013 2012 2011 2010 2009 2008 2007 2006 2005 2004 2003 2002 2001 2000 1999 1998 1997 1996 1995 1994 1993 1992 1991 1990
do
        echo "perl FetchEvent-2014.310.pl -s $i-01-01 -e `expr $i + 1`-01-01  -X $i-`expr $i + 1`.xml &" 
        perl FetchEvent-2014.310.pl -vv -s $i-01-01 -e `expr $i + 1`-01-01  -X $i-`expr $i + 1`.xml 
done
