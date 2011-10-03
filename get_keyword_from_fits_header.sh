function get_keyword_from_fits_header
{
    #use only the packaged version of wcstools
    WCSTOOLS=wcstools-local/bin

    if (( $# != 2 )); then
	echo "Function get_keyword_from_fits_header requires two arguments:"
	echo "get_keyword_from_fits_header fits-file keyword"
	exit 1
    fi

    file=$1
    keyword=$2

    echo $($WCSTOOLS/gethead -b $file $keyword)
    return
}