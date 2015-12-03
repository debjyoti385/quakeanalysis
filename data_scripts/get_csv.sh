for i in 2015 2014 2013 2012 2011 2010 2009 2008 2007 2006 2005 2004 2003 2002 2001 2000 1999 1998 1997 1996 1995 1994 1993 1992 1991 1990
do
        mkdir $i
        echo "mkdir $i"
        cd $i
        echo "cd $i"
        cp ../$i-`expr $i + 1`.xml  .
        echo "cp ../$i-`expr $i + 1`.xml  ".
        xml_split -l 2 -s 10Mb  $i-`expr $i + 1`.xml
        echo "xml_split -l 2 -s 10Mb  $i-`expr $i + 1`.xml"
        rm $i-`expr $i + 1`.xml
        ls *.xml  | xargs -I {} python ../EventToCsv.py {} {}.csv
        cat *.csv > $i-`expr $i + 1`.csv
        mv $i-`expr $i + 1`.csv ../
        cd ..
        rm -rf $i
done



