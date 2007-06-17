# bash completion for project-builder.  Must have the bash-completion package
# installed to use this, because of use of _filedir

_project_builder_platforms()
{
    local platforms="$(project-builder -c list-platforms)"
    COMPREPLY=( ${COMPREPLY[@]:-} $(compgen -W "$platforms" -- "$cur") )
}

_project_builder_projects()
{
    local projects="$(project-builder -c list-projects | cut -f 1 -d ' ')"
    COMPREPLY=( ${COMPREPLY[@]:-} $(compgen -W "$projects" -- "$cur") )
}

_project_builder()
{
    local cur prev

    COMPREPLY=()
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    case $prev in
        -@(-command|c))
            COMPREPLY=( $( compgen -W '\
                create-install-iso \
                create-install-usb \
                create-live-iso \
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
                update-project \
                update-target \
		chroot-project \
		chroot-target \
                ' -- $cur  ) )
            return 0
            ;;
        --platform-name)
            _project_builder_platforms
            return 0
            ;;
        --project-name)
            _project_builder_projects
            return 0
            ;;
    esac

    if [[ "$cur" == -* ]] ; then
        COMPREPLY=( $( compgen -W '
        -c --command --platform-name \
        --project-name --project-description \
        --project-path -t --target-name \
        --fset-name --image-name -q --quiet \
        -d --enable-debug -h --help' -- $cur ) )
    else
        _filedir
    fi
}
complete -F _project_builder $filenames project-builder
