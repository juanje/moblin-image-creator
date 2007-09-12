# bash completion for Moblin image-creator.  Must have the bash-completion
# package installed to use this, because of use of _filedir

_image_creator_platforms()
{
    local platforms="$(image-creator -c list-platforms)"
    COMPREPLY=( ${COMPREPLY[@]:-} $(compgen -W "$platforms" -- "$cur") )
}

_image_creator_projects()
{
    local projects="$(image-creator -c list-projects | cut -f 1 -d ' ')"
    COMPREPLY=( ${COMPREPLY[@]:-} $(compgen -W "$projects" -- "$cur") )
}

_image_creator()
{
    local cur prev

    COMPREPLY=()
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    case $prev in
        -@(-command|c))
            COMPREPLY=( $( compgen -W '\
                chroot-project \
                chroot-target \
                clear-rootstraps \
                create-install-usb \
                create-live-usb \
                create-project \
                create-target \
                delete-project \
                delete-target \
                install-fset \
                list-fsets \
                list-platforms \
                list-projects \
                list-targets \
                load-project \
                run-project \
                run-target \
                save-project \
                umount-project \
                umount-target \
                update-project \
                update-target \
                ' -- $cur  ) )
            return 0
            ;;
        --platform-name)
            _image_creator_platforms
            return 0
            ;;
        --project-name)
            _image_creator_projects
            return 0
            ;;
    esac

    if [[ "$cur" == -* ]] ; then
        COMPREPLY=( $( compgen -W '
            --bypass-rootstrap \
            --command \
            --enable-debug \
            --file-name \
            --fset-name \
            --help \
            --image-name \
            --platform-name \
            --project-description \
            --project-name \
            --project-path \
            --quiet \
            --run-command \
            --target-name \
            -c \
            -d \
            -f \
            -h \
            -q \
            -t \
        ' -- $cur ) )
    else
        _filedir
    fi
}
complete -F _image_creator $filenames image-creator
