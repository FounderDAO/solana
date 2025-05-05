
##  Убедись, что нужное ядро установлено:
dpkg -l | grep linux-image

## Если нет — установи:
sudo apt update &&
sudo apt install linux-image-6.8.0-53-generic linux-headers-6.8.0-53-generic

## Посмотри список доступных ядер в GRUB:
grep menuentry /boot/grub/grub.cfg | cut -d "'" -f2

## Открой GRUB-конфиг:
sudo nano +6 /etc/default/grub

## Найди строку:
GRUB_DEFAULT=0

## Замени её на:
GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-53-generic"

##  Обнови GRUB:
sudo update-grub

## Перезагрузи сервер:
sudo reboot

## После перезагрузки проверь:
uname -r && uname -rs

```bash
pub fn process_next_vote_slot(&mut self, next_vote_slot: Slot) {
        // Ignore votes for slots earlier than we already have votes for
        if self
            .last_voted_slot()
            .is_some_and(|last_voted_slot| next_vote_slot <= last_voted_slot)
        {
            return;
        }

        self.pop_expired_votes(next_vote_slot);

        // Once the stack is full, pop the oldest lockout and distribute rewards
        if self.votes.len() == MAX_LOCKOUT_HISTORY {
            let rooted_vote = self.votes.pop_front().unwrap();
            self.root_slot = Some(rooted_vote.slot());
        }
        self.votes.push_back(Lockout::new(next_vote_slot));
        self.double_lockouts();
    }
```

```bash
pub fn process_next_vote_slot(&mut self, next_vote_slot: Slot) {
        // Ignore votes for slots earlier than we already have votes for
        if self
            .last_voted_slot()
            .is_some_and(|last_voted_slot| next_vote_slot <= last_voted_slot)
        {
            return;
        }

        self.pop_expired_votes(next_vote_slot);

        // Once the stack is full, pop the oldest lockout and distribute rewards
        if self.votes.len() == MAX_LOCKOUT_HISTORY {
            let rooted_vote = self.votes.pop_front().unwrap();
            self.root_slot = Some(rooted_vote.slot());
        }
        self.votes.push_back(Lockout::new(next_vote_slot));
        self.double_lockouts();
    }
```