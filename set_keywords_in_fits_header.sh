function set_keywords_in_fits_header
{

    #use only the packaged version of wcstools
    WCSTOOLS=wcstools-local/bin

    file=$1; shift;

    keywords="$@"
    #echo $#
    $WCSTOOLS/sethead -h $file "$@"
}