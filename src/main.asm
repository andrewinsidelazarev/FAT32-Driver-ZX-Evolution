        DEVICE ZXSPECTRUM128
        INCLUDE "fat32.inc"
        INCLUDE "filex.inc"
        INCLUDE "extension_ids.inc"
        ORG FAT32_BASE

API_TABLE:
        JP DRIVER_BIND                   ; 0
        JP FAT_DEVICE_INIT               ; 1
        JP FAT_INFO                      ; 2
        JP FAT_MOUNT                     ; 3
        JP WDOS.RDD                      ; 4
        JP WDOS.SDD                      ; 5
        JP WDOS.GIPAG                    ; 6
        JP FAT_READ                      ; 7
        JP FAT_WRITE                     ; 8
        JP DRIVER_BIND                   ; 9
        JP WDOS.GLSTCAT                  ; 10
        JP WDOS.TLSTCAT                  ; 11
        JP WDOS.SRHFCL                   ; 12
        JP FAT_APPEND                    ; 13: для APPEND также есть вход 76
        JP WDOS.MKSG                     ; 14
        JP FAT_FILEX                     ; 15: для FILEX также есть вход 77
        JP WDOS.RFRH                     ; 16
        JP WDOS.GENTRY                   ; 17
        JP WDOS.TENTRY                   ; 18
        JP FAT_CREATE                    ; 19
        JP FAT_MKDIR                     ; 20
        JP FAT_DELETE                    ; 21
        JP FAT_RENAME                    ; 22
        JP WDOS.DLSG                     ; 23
        JP WDOS.CHTOSE                   ; 24
        JP FAT_NOT_SUPPORTED             ; 25
        JP FAT_FIND                      ; 26
        JP WDOS.LOAD256                  ; 27
        JP WDOS.LOADNON                  ; 28
        JP WDOS.NXTETY                   ; 29
        JP WDOS.NXTETY2                  ; 30
        JP FAT_SET_DIR                   ; 31
        JP FAT_SET_ROOT                  ; 32
        JP FAT_SEEK_START                ; 33
        JP FAT_SYNC                      ; 34
        JP FAT_CLOSE                     ; 35
        JP FAT_MOUNT_AT                  ; 36
        DUP 11                          ; 37..47
        JP FAT_NOT_SUPPORTED
        EDUP
        JP FAT_READ                      ; 48: LOAD512
        JP FAT_WRITE                     ; 49: SAVE512
        JP FAT_SEEK_START                ; 50: GIPAGPL
        JP WDOS.TENTRY                   ; 51: TENTRY
        JP WDOS.CHTOSE                   ; 52: CHTOSEP
        JP FAT_NOT_SUPPORTED             ; 53
        JP FAT_NOT_SUPPORTED             ; 54: отметка в интерфейсе — задача приложения
        JP FAT_NOT_SUPPORTED             ; 55
        JP FAT_SET_DIR                   ; 56: ADIR
        JP FAT_NOT_SUPPORTED             ; 57: STREAM переключает панели WC
        JP WDOS.NXTETY2                  ; 58
        JP FAT_FIND                      ; 59
        JP WDOS.LOAD256                  ; 60
        JP WDOS.LOADNON                  ; 61
        JP FAT_SEEK_START                ; 62: GFILE
        JP FAT_SET_DIR                   ; 63: GDIR
        DUP 8                           ; 64..71
        JP FAT_NOT_SUPPORTED
        EDUP
        JP FAT_CREATE                    ; 72: MKFILE
        JP FAT_MKDIR                     ; 73
        JP FAT_RENAME                    ; 74
        JP FAT_DELETE                    ; 75
        JP FAT_APPEND                    ; 76: полный APPEND
        JP FAT_FILEX                     ; 77: полный FILEX
        DUP FAT32_COMMAND_COUNT-78       ; запас для команд 78..127
        JP FAT_NOT_SUPPORTED
        EDUP
API_TABLE_END:
        ASSERT API_TABLE_END-API_TABLE == FAT32_COMMAND_COUNT*3

        MODULE WDOS
        INCLUDE "state.inc"
START EQU @API_TABLE
        INCLUDE "core32.asm"
        ENDMODULE
        MODULE WDOS_EXT
        INCLUDE "extension.asm"
        ENDMODULE
        INCLUDE "filex.asm"
        INCLUDE "public.asm"
        INCLUDE "block_io.asm"
CODE_END:
        ASSERT CODE_END <= #8000, FAT32 code exceeds the 16 KiB code window
        SAVEBIN "build/fat32.bin",FAT32_BASE,CODE_END-FAT32_BASE
